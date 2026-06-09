import 'dart:convert';
import 'dart:html' as html;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../models/user.dart';
import '../config/constants.dart';

/// Auth state provider managing local Operator ID authentication.
final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() => const AuthState();

  /// Initialize local Operator ID session (call once at app startup).
  Future<void> initialize() async {
    // Try to load cached Operator ID from browser local storage
    try {
      final savedToken = html.window.localStorage['operator_id'];
      if (savedToken != null && savedToken.trim().isNotEmpty) {
        state = AuthState(
          user: AppUser(
            userId: savedToken,
            email: '$savedToken@scp.foundation',
            name: savedToken,
            picture: '',
            idToken: savedToken,
          ),
        );
      }
    } catch (_) {
      // Local storage may fail in some sandboxed environments, ignore
    }
  }

  /// Perform local Operator ID Sign-In
  Future<void> signIn(String operatorId) async {
    if (operatorId.trim().isEmpty) return;
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await http.post(
        Uri.parse('${AppConstants.apiBaseUrl}/api/auth/verify'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'id_token': operatorId}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final userMap = data['user'];
        final user = AppUser(
          userId: userMap['user_id'],
          email: userMap['email'],
          name: userMap['name'],
          picture: userMap['picture'] ?? '',
          idToken: operatorId,
        );

        // Cache in browser local storage
        try {
          html.window.localStorage['operator_id'] = operatorId;
        } catch (_) {}
        
        state = AuthState(user: user, isLoading: false);
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Access Denied: HTTP ${response.statusCode}',
        );
      }
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Sign out.
  Future<void> signOut() async {
    try {
      html.window.localStorage.remove('operator_id');
    } catch (_) {}
    state = const AuthState();
  }
}
