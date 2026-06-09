import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;
import '../config/constants.dart';
import '../config/theme.dart';

/// Splash screen — waits for backend to be ready before allowing login.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;
  String _status = 'Initializing systems...';

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );
    _fadeAnimation = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeInOut,
    );
    _fadeController.forward();
    _waitForBackend();
  }

  /// Poll the health endpoint until the backend is ready.
  /// Cloud Run cold start returns 503 (no CORS headers) until the container
  /// is up. We wait here so the chat screen never hits that window.
  Future<void> _waitForBackend() async {
    const maxWaitSeconds = 360; // 6 minutes
    const pollInterval = Duration(seconds: 8);
    int elapsed = 0;

    while (elapsed < maxWaitSeconds) {
      try {
        final response = await http
            .get(Uri.parse('${AppConstants.apiBaseUrl}/health'))
            .timeout(const Duration(seconds: 10));

        // Any JSON response means FastAPI is up (even if degraded)
        if (response.statusCode < 500) {
          try {
            jsonDecode(response.body);
            // Backend responded with JSON → ready
            if (mounted) context.go('/login');
            return;
          } catch (_) {
            // Not JSON → still cold-starting (Cloud Run infra 503)
          }
        }
      } catch (_) {
        // Connection refused / timeout → still cold-starting
      }

      elapsed += pollInterval.inSeconds;
      if (mounted) {
        setState(() {
          _status = '서버 시작 중...';
        });
      }
      await Future.delayed(pollInterval);
    }

    // Timed out — proceed anyway and let the chat screen handle errors
    if (mounted) context.go('/login');
  }

  @override
  void dispose() {
    _fadeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: FadeTransition(
          opacity: _fadeAnimation,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // SCP Logo
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: SCPTheme.scpGold, width: 3),
                ),
                child: const Center(
                  child: Text(
                    'SCP',
                    style: TextStyle(
                      fontSize: 36,
                      fontWeight: FontWeight.w900,
                      color: SCPTheme.scpGold,
                      letterSpacing: 6,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                'SCP WORLD',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: SCPTheme.scpGold,
                  letterSpacing: 8,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'SECURE. CONTAIN. PROTECT.',
                style: TextStyle(
                  fontSize: 12,
                  color: SCPTheme.textSecondary,
                  letterSpacing: 4,
                ),
              ),
              const SizedBox(height: 48),
              const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: SCPTheme.accentRed,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                _status,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 12,
                  color: SCPTheme.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
