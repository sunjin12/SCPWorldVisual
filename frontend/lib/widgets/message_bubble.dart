import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../models/message.dart';

/// Chat message bubble with SCP styling.
class MessageBubble extends StatelessWidget {
  final Message message;

  const MessageBubble({super.key, required this.message});

  bool get isUser => message.role == 'user';

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            // AI Avatar
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: SCPTheme.accentRed.withValues(alpha: 0.2),
                border: Border.all(
                  color: SCPTheme.accentRed.withValues(alpha: 0.5),
                ),
              ),
              child: const Icon(
                Icons.smart_toy,
                size: 16,
                color: SCPTheme.accentRed,
              ),
            ),
            const SizedBox(width: 8),
          ],
          // Message content
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: isUser
                    ? SCPTheme.accentRed.withValues(alpha: 0.15)
                    : SCPTheme.surfaceCard,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(isUser ? 16 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 16),
                ),
                border: Border.all(
                  color: isUser
                      ? SCPTheme.accentRed.withValues(alpha: 0.3)
                      : const Color(0xFF2A2A4A),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Role label
                  Text(
                    isUser ? 'YOU' : 'SCP FOUNDATION',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: isUser ? SCPTheme.accentRed : SCPTheme.scpGold,
                      letterSpacing: 1.5,
                    ),
                  ),
                  const SizedBox(height: 6),
                  // Stage indicator (shown while streaming, before tokens arrive)
                  if (!isUser && message.isStreaming && message.content.isEmpty)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const SizedBox(
                            width: 10,
                            height: 10,
                            child: CircularProgressIndicator(
                              strokeWidth: 1.5,
                              color: SCPTheme.scpGold,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _stageLabel(message.stage),
                            style: const TextStyle(
                              fontSize: 12,
                              color: SCPTheme.textSecondary,
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                        ],
                      ),
                    ),
                  // Error display
                  if (message.errorText != null)
                    Text(
                      '⚠ ${message.errorText!}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: SCPTheme.accentRed,
                      ),
                    ),
                  // Message text with [REDACTED] styling
                  if (message.content.isNotEmpty) _buildStyledText(message.content),
                  // Streaming indicator
                  if (message.isStreaming && message.content.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: _buildCursor(),
                    ),
                ],
              ),
            ),
          ),
          if (isUser) const SizedBox(width: 40),
        ],
      ),
    );
  }

  String _stageLabel(String? stage) {
    switch (stage) {
      case null:
        return '서버 연결 중...';
      case 'history':
        return '세션 기록 불러오는 중...';
      case 'rag':
        return '연구 일지 조회 중...';
      case 'prompt':
        return '문서 분석 중...';
      case 'llm':
        return '답변 생성 중...';
      case 'persist':
        return '기록 저장 중...';
      default:
        return '처리 중...';
    }
  }

  /// Style [REDACTED] and [DATA EXPUNGED] as black boxes.
  Widget _buildStyledText(String text) {
    final pattern = RegExp(r'\[REDACTED\]|\[DATA EXPUNGED\]|\[█+\]');
    final spans = <InlineSpan>[];
    int lastEnd = 0;

    for (final match in pattern.allMatches(text)) {
      if (match.start > lastEnd) {
        spans.add(TextSpan(
          text: text.substring(lastEnd, match.start),
          style: const TextStyle(
            fontSize: 14,
            color: SCPTheme.textPrimary,
            height: 1.5,
          ),
        ));
      }
      spans.add(WidgetSpan(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
          decoration: BoxDecoration(
            color: SCPTheme.redactedBlack,
            borderRadius: BorderRadius.circular(2),
          ),
          child: Text(
            match.group(0)!,
            style: const TextStyle(
              fontSize: 12,
              color: SCPTheme.redactedBlack,
              fontWeight: FontWeight.w700,
              letterSpacing: 1,
            ),
          ),
        ),
      ));
      lastEnd = match.end;
    }

    if (lastEnd < text.length) {
      spans.add(TextSpan(
        text: text.substring(lastEnd),
        style: const TextStyle(
          fontSize: 14,
          color: SCPTheme.textPrimary,
          height: 1.5,
        ),
      ));
    }

    return RichText(text: TextSpan(children: spans));
  }

  /// Blinking cursor for streaming effect.
  Widget _buildCursor() {
    return const _BlinkingCursor();
  }
}

class _BlinkingCursor extends StatefulWidget {
  const _BlinkingCursor();

  @override
  State<_BlinkingCursor> createState() => _BlinkingCursorState();
}

class _BlinkingCursorState extends State<_BlinkingCursor>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _controller,
      child: Container(
        width: 8,
        height: 16,
        color: SCPTheme.accentRed,
      ),
    );
  }
}
