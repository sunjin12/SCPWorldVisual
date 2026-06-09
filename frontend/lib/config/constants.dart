/// API and configuration constants.
class AppConstants {
  AppConstants._();

  /// Backend API base URL (override for production)
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  /// SSE streaming endpoint
  static const String chatStreamEndpoint = '/api/chat/stream';
}
