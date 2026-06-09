/// Authenticated user model.
class AppUser {
  final String userId;
  final String email;
  final String name;
  final String picture;
  final String idToken;

  const AppUser({
    required this.userId,
    required this.email,
    required this.name,
    this.picture = '',
    required this.idToken,
  });

  bool get isLoggedIn => userId.isNotEmpty;
}

/// Authentication state.
class AuthState {
  final AppUser? user;
  final bool isLoading;
  final String? error;

  const AuthState({this.user, this.isLoading = false, this.error});

  bool get isLoggedIn => user != null;
  String get idToken => user?.idToken ?? '';

  AuthState copyWith({AppUser? user, bool? isLoading, String? error}) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}
