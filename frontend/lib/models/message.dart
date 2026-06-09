/// Chat message model.
class Message {
  final String role; // 'user' or 'assistant'
  final String content;
  final DateTime timestamp;
  final bool isStreaming;
  final String? stage;
  final String? errorText;

  Message({
    required this.role,
    required this.content,
    DateTime? timestamp,
    this.isStreaming = false,
    this.stage,
    this.errorText,
  }) : timestamp = timestamp ?? DateTime.now();

  Message copyWith({String? content, bool? isStreaming, String? stage, String? errorText}) {
    return Message(
      role: role,
      content: content ?? this.content,
      timestamp: timestamp,
      isStreaming: isStreaming ?? this.isStreaming,
      stage: stage ?? this.stage,
      errorText: errorText ?? this.errorText,
    );
  }
}
