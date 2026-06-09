import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import '../config/theme.dart';
import '../providers/auth_provider.dart';
import '../providers/chat_provider.dart';
import '../providers/persona_provider.dart';
import '../widgets/message_bubble.dart';
import '../widgets/footer.dart';
import '../widgets/visual_monitor.dart';

/// Main chat screen with SSE streaming.
class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();

  void _sendMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    ref.read(chatProvider.notifier).sendMessage(text);
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(chatProvider);
    final persona = ref.watch(selectedPersonaProvider);
    final auth = ref.watch(authProvider);

    // Auto-scroll when messages update
    ref.listen(chatProvider, (prev, next) {
      if (prev?.messages.length != next.messages.length ||
          (next.messages.isNotEmpty && next.messages.last.isStreaming)) {
        _scrollToBottom();
      }
    });

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/personas'),
        ),
        title: Text(persona?.name ?? 'SCP WORLD'),
        actions: [
          // New session
          IconButton(
            icon: const Icon(Icons.add_comment_outlined, size: 20),
            tooltip: 'New Session',
            onPressed: () => ref.read(chatProvider.notifier).newSession(),
          ),
          // User info / logout menu
          if (auth.user != null)
            Padding(
              padding: const EdgeInsets.only(right: 12),
              child: PopupMenuButton<String>(
                tooltip: 'Account',
                offset: const Offset(0, 44),
                color: SCPTheme.surfaceCard,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                  side: const BorderSide(color: Color(0xFF2A2A4A)),
                ),
                onSelected: (value) async {
                  if (value == 'logout') {
                    await ref.read(authProvider.notifier).signOut();
                    ref.read(chatProvider.notifier).newSession();
                  }
                },
                itemBuilder: (context) => [
                  PopupMenuItem<String>(
                    enabled: false,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          auth.user!.name.isNotEmpty ? auth.user!.name : 'Operator',
                          style: const TextStyle(
                            fontSize: 13,
                            color: SCPTheme.textPrimary,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          auth.user!.email,
                          style: const TextStyle(
                            fontSize: 11,
                            color: SCPTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const PopupMenuDivider(),
                  const PopupMenuItem<String>(
                    value: 'logout',
                    child: Row(
                      children: [
                        Icon(Icons.logout, size: 16, color: SCPTheme.accentRed),
                        SizedBox(width: 8),
                        Text(
                          'LOG OUT',
                          style: TextStyle(
                            fontSize: 13,
                            color: SCPTheme.accentRed,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 1.2,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
                child: CircleAvatar(
                  radius: 16,
                  backgroundColor: SCPTheme.surfaceCard,
                  child: Text(
                    auth.user!.name.isNotEmpty
                        ? auth.user!.name[0].toUpperCase()
                        : '?',
                    style: const TextStyle(
                      fontSize: 14,
                      color: SCPTheme.scpGold,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isWide = constraints.maxWidth >= 800;

          final monitorWidget = Padding(
            padding: const EdgeInsets.all(16.0),
            child: persona != null
                ? VisualMonitor(persona: persona)
                : const SizedBox(),
          );

          final chatInterfaceWidget = Column(
            children: [
              // Messages list
              Expanded(
                child: chatState.messages.isEmpty
                    ? _buildEmptyState()
                    : ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 12,
                        ),
                        itemCount: chatState.messages.length,
                        itemBuilder: (context, index) {
                          return MessageBubble(
                            message: chatState.messages[index],
                          );
                        },
                      ),
              ),

              // Error display
              if (chatState.error != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  color: SCPTheme.accentRed.withValues(alpha: 0.1),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline,
                          color: SCPTheme.accentRed, size: 16),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          chatState.error!,
                          style: const TextStyle(
                            fontSize: 12,
                            color: SCPTheme.accentRed,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),

              // Input bar
              _buildInputBar(chatState.isLoading),

              // Footer
              const SCPFooter(),
            ],
          );

          if (isWide) {
            return Row(
              children: [
                Expanded(
                  flex: 4,
                  child: monitorWidget,
                ),
                const VerticalDivider(width: 1, color: Color(0xFF2A2A4A)),
                Expanded(
                  flex: 6,
                  child: chatInterfaceWidget,
                ),
              ],
            );
          } else {
            return Column(
              children: [
                Container(
                  height: 220,
                  width: double.infinity,
                  child: monitorWidget,
                ),
                const Divider(height: 1, color: Color(0xFF2A2A4A)),
                Expanded(
                  child: chatInterfaceWidget,
                ),
              ],
            );
          }
        },
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.chat_bubble_outline,
            size: 64,
            color: SCPTheme.textSecondary.withValues(alpha: 0.3),
          ),
          const SizedBox(height: 16),
          const Text(
            'SCP DATABASE TERMINAL',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: SCPTheme.textSecondary,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Enter your query to access SCP records.',
            style: TextStyle(
              fontSize: 12,
              color: SCPTheme.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputBar(bool isLoading) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: const BoxDecoration(
        color: SCPTheme.surfaceDark,
        border: Border(
          top: BorderSide(color: Color(0xFF2A2A4A), width: 1),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: KeyboardListener(
              focusNode: FocusNode(),
              onKeyEvent: (event) {
                if (event is KeyDownEvent &&
                    event.logicalKey == LogicalKeyboardKey.enter &&
                    !HardwareKeyboard.instance.isShiftPressed) {
                  if (!isLoading) _sendMessage();
                }
              },
              child: TextField(
                controller: _controller,
                enabled: !isLoading,
                maxLines: 5,
                minLines: 1,
                textInputAction: TextInputAction.newline,
                onChanged: (value) {
                  // Force layout update for multi-line growth
                  setState(() {});
                },
                style:
                    const TextStyle(fontSize: 14, color: SCPTheme.textPrimary),
                decoration: InputDecoration(
                  hintText: isLoading
                      ? 'Processing query...'
                      : 'Enter query (e.g., "Tell me about SCP-173")',
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            decoration: BoxDecoration(
              color: isLoading ? SCPTheme.surfaceCard : SCPTheme.accentRed,
              borderRadius: BorderRadius.circular(12),
            ),
            child: IconButton(
              icon: isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.send, size: 20),
              color: Colors.white,
              onPressed: isLoading ? null : _sendMessage,
            ),
          ),
        ],
      ),
    );
  }
}
