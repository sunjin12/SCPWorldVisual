import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'config/theme.dart';
import 'screens/login_screen.dart';
import 'screens/persona_select_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/splash_screen.dart';
import 'providers/auth_provider.dart';

/// GoRouter configuration with auth guard.
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/splash',
    redirect: (context, state) {
      final isLoggedIn = authState.isLoggedIn;
      final currentPath = state.matchedLocation;

      // Allow splash and login without auth
      if (currentPath == '/splash') return null;
      if (currentPath == '/login' && isLoggedIn) return '/personas';
      if (currentPath != '/login' && !isLoggedIn) return '/login';
      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (_, __) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (_, __) => const LoginScreen(),
      ),
      GoRoute(
        path: '/personas',
        builder: (_, __) => const PersonaSelectScreen(),
      ),
      GoRoute(
        path: '/chat',
        builder: (_, __) => const ChatScreen(),
      ),
    ],
  );
});

class SCPWorldApp extends ConsumerWidget {
  const SCPWorldApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'SCP World',
      debugShowCheckedModeBanner: false,
      theme: SCPTheme.darkTheme,
      routerConfig: router,
    );
  }
}
