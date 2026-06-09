import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';
import '../config/constants.dart';
import '../models/message.dart';
import 'auth_provider.dart';
import 'persona_provider.dart';

/// Chat state holding messages and session info for ONE persona.
class ChatState {
  final List<Message> messages;
  final String sessionId;
  final bool isLoading;
  final String? error;

  const ChatState({
    this.messages = const [],
    required this.sessionId,
    this.isLoading = false,
    this.error,
  });

  ChatState copyWith({
    List<Message>? messages,
    bool? isLoading,
    String? error,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      sessionId: sessionId,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// Per-persona chat sessions. Switching personas swaps the visible state to
/// that persona's own message thread; sending a message under one persona
/// never appears in another's history. The backend session_id is also
/// per-persona, so server-side history (SQLite) stays segregated too.
final chatProvider = NotifierProvider<ChatNotifier, ChatState>(ChatNotifier.new);

class ChatNotifier extends Notifier<ChatState> {
  final Map<String, ChatState> _sessions = {};

  @override
  ChatState build() {
    final persona = ref.watch(selectedPersonaProvider);
    final personaId = persona?.id ?? 'researcher';
    return _sessions.putIfAbsent(
      personaId,
      () => ChatState(sessionId: const Uuid().v4()),
    );
  }

  String _activePersonaId() {
    final persona = ref.read(selectedPersonaProvider);
    return persona?.id ?? 'researcher';
  }

  /// Persist per-persona session and only push to the visible `state` if the
  /// user is still viewing this persona (they may have switched mid-stream).
  void _writeSession(String personaId, ChatState newState) {
    _sessions[personaId] = newState;
    if (_activePersonaId() == personaId) {
      state = newState;
    }
  }

  /// Send a message and receive SSE streaming response.
  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    final authState = ref.read(authProvider);
    if (!authState.isLoggedIn) return;

    final personaId = _activePersonaId();
    var session = _sessions.putIfAbsent(
      personaId,
      () => ChatState(sessionId: const Uuid().v4()),
    );

    // Add user message
    final userMsg = Message(role: 'user', content: text);
    session = session.copyWith(
      messages: [...session.messages, userMsg],
      isLoading: true,
      error: null,
    );
    _writeSession(personaId, session);

    // Add placeholder for streaming AI response
    final aiMsg = Message(role: 'assistant', content: '', isStreaming: true);
    session = session.copyWith(messages: [...session.messages, aiMsg]);
    _writeSession(personaId, session);

    try {
      final request = http.Request(
        'POST',
        Uri.parse('${AppConstants.apiBaseUrl}${AppConstants.chatStreamEndpoint}'),
      );
      request.headers['Authorization'] = 'Bearer ${authState.idToken}';
      request.headers['Content-Type'] = 'application/json';
      request.body = jsonEncode({
        'session_id': session.sessionId,
        'message': text,
        'persona_id': personaId,
      });

      final response = await http.Client().send(request);
      final stream = response.stream
          .transform(utf8.decoder)
          .transform(const LineSplitter());

      String fullContent = '';
      bool streamDone = false;

      await for (final line in stream) {
        if (!line.startsWith('data: ')) continue;

        final jsonStr = line.substring(6).trim();
        if (jsonStr.isEmpty) continue;

        try {
          final data = jsonDecode(jsonStr);
          if (data['error'] != null) {
            final msgs = List<Message>.from(session.messages);
            msgs[msgs.length - 1] = msgs.last.copyWith(
              errorText: '[${data['stage'] ?? 'error'}] ${data['error']}',
              isStreaming: false,
            );
            session = session.copyWith(messages: msgs);
            _writeSession(personaId, session);
            streamDone = true;
            break;
          }
          if (data['stage'] != null) {
            final msgs = List<Message>.from(session.messages);
            msgs[msgs.length - 1] = msgs.last.copyWith(
              stage: data['stage'] as String,
            );
            session = session.copyWith(messages: msgs);
            _writeSession(personaId, session);
            continue;
          }
          if (data['done'] == true) {
            // Backend applied post-processing (language/token filter) to the
            // full response. Replace the streamed buffer with the cleaned
            // version so the user sees the sanitized text.
            final finalText = data['final_text'];
            if (finalText is String && finalText.isNotEmpty) {
              fullContent = finalText;
              final msgs = List<Message>.from(session.messages);
              msgs[msgs.length - 1] = msgs.last.copyWith(
                content: fullContent,
                stage: 'llm',
              );
              session = session.copyWith(messages: msgs);
              _writeSession(personaId, session);
            }
            streamDone = true;
            break;
          }
          if (data['token'] != null) {
            fullContent += data['token'] as String;
            final msgs = List<Message>.from(session.messages);
            msgs[msgs.length - 1] = msgs.last.copyWith(
              content: fullContent,
              stage: 'llm',
            );
            session = session.copyWith(messages: msgs);
            _writeSession(personaId, session);
          }
        } catch (_) {
          // Skip malformed SSE lines
        }
      }

      // Mark streaming as complete
      final msgs = List<Message>.from(session.messages);
      final lastMsg = msgs.last;
      if (!streamDone && lastMsg.content.isEmpty && lastMsg.errorText == null) {
        // 스트림이 done/error 없이 닫힘 — 콜드스타트 중 연결 끊김
        msgs[msgs.length - 1] = lastMsg.copyWith(
          isStreaming: false,
          errorText: '서버 응답이 없습니다. 콜드스타트 중이라면 잠시 후 다시 시도해 주세요.',
        );
      } else {
        msgs[msgs.length - 1] = lastMsg.copyWith(isStreaming: false);
      }
      session = session.copyWith(messages: msgs, isLoading: false);
      _writeSession(personaId, session);
    } catch (e) {
      // Remove the empty AI placeholder on error
      final msgs = List<Message>.from(session.messages);
      if (msgs.isNotEmpty && msgs.last.role == 'assistant' && msgs.last.content.isEmpty) {
        msgs.removeLast();
      }
      session = session.copyWith(
        messages: msgs,
        isLoading: false,
        error: e.toString(),
      );
      _writeSession(personaId, session);
    }
  }

  /// Start a new session for the currently-selected persona only.
  void newSession() {
    final personaId = _activePersonaId();
    final fresh = ChatState(sessionId: const Uuid().v4());
    _writeSession(personaId, fresh);
  }
}
