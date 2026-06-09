import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../config/theme.dart';
import '../providers/auth_provider.dart';

/// Login screen with local Operator ID entry.
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _idController = TextEditingController();

  @override
  void dispose() {
    _idController.dispose();
    super.dispose();
  }

  void _submit() {
    final id = _idController.text.trim();
    if (id.isEmpty) return;
    ref.read(authProvider.notifier).signIn(id);
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);

    // Navigate on successful login
    ref.listen(authProvider, (prev, next) {
      if (next.isLoggedIn) {
        context.go('/personas');
      }
    });

    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // SCP Emblem
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: SCPTheme.scpGold, width: 2),
                ),
                child: const Center(
                  child: Text(
                    'SCP',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w900,
                      color: SCPTheme.scpGold,
                      letterSpacing: 4,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 32),
              const Text(
                'SCP WORLD',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                  color: SCPTheme.scpGold,
                  letterSpacing: 6,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'AI Persona Chatbot',
                style: TextStyle(
                  fontSize: 14,
                  color: SCPTheme.textSecondary,
                ),
              ),
              const SizedBox(height: 48),

              // Authorization notice
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: SCPTheme.surfaceCard,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: SCPTheme.accentRed.withValues(alpha: 0.3),
                  ),
                ),
                child: const Column(
                  children: [
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.warning_amber, color: SCPTheme.warningAmber, size: 18),
                        SizedBox(width: 8),
                        Text(
                          'LEVEL 2 CLEARANCE REQUIRED',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: SCPTheme.warningAmber,
                            letterSpacing: 2,
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 8),
                    Text(
                      'Authenticate with your Foundation credentials to access the SCP Database.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 12,
                        color: SCPTheme.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),

              // Operator ID Input Form
              Container(
                constraints: const BoxConstraints(maxWidth: 400),
                child: Column(
                  children: [
                    TextField(
                      controller: _idController,
                      enabled: !authState.isLoading,
                      style: const TextStyle(
                        color: SCPTheme.scpGold,
                        fontFamily: 'monospace',
                        letterSpacing: 1.2,
                      ),
                      decoration: const InputDecoration(
                        labelText: 'ENTER OPERATOR CLEARANCE ID',
                        labelStyle: TextStyle(
                          color: SCPTheme.textSecondary,
                          fontSize: 11,
                          letterSpacing: 1.5,
                        ),
                        hintText: 'e.g. OP-104 or Username',
                        hintStyle: TextStyle(color: Color(0xFF4A4A6A), fontSize: 13),
                        enabledBorder: OutlineInputBorder(
                          borderSide: BorderSide(color: Color(0xFF2A2A4A)),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderSide: BorderSide(color: SCPTheme.scpGold),
                        ),
                      ),
                      onSubmitted: (_) => _submit(),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton.icon(
                        onPressed: authState.isLoading ? null : _submit,
                        icon: authState.isLoading
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.security, size: 20),
                        label: Text(
                          authState.isLoading
                              ? 'INITIALIZING LINK...'
                              : 'INITIALIZE ACCESS',
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 1.2,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Error display
              if (authState.error != null) ...[
                const SizedBox(height: 16),
                Text(
                  authState.error!,
                  style: const TextStyle(color: SCPTheme.accentRed, fontSize: 12),
                  textAlign: TextAlign.center,
                ),
              ],

              const SizedBox(height: 48),

              // Footer
              const Text(
                'Content based on the SCP Foundation Wiki (CC-BY-SA 3.0)',
                style: TextStyle(fontSize: 10, color: SCPTheme.textSecondary),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
