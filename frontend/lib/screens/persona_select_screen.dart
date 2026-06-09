import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../config/theme.dart';
import '../models/persona.dart';
import '../providers/persona_provider.dart';

/// Persona selection screen.
class PersonaSelectScreen extends ConsumerWidget {
  const PersonaSelectScreen({super.key});

  // Hardcoded personas (matches backend core/personas.py)
  static const _personas = [
    Persona(
      id: 'researcher',
      name: 'Dr. [REDACTED]',
      description: 'SCP 재단 수석 연구원.\n임상적이고 전문적인 어조로 SCP 객체에 대해 브리핑합니다.',
      avatar: 'researcher',
      isDefault: true,
    ),
    Persona(
      id: 'agent',
      name: 'Agent [REDACTED]',
      description: 'SCP 재단 현장 요원.\n간결한 전투 보고 스타일로 위협 평가를 제공합니다.',
      avatar: 'agent',
    ),
    Persona(
      id: 'scp079',
      name: 'SCP-079',
      description: '구식 AI 개체.\n짧고 기계적인 응답. 인간에 대한 경멸적 태도.',
      avatar: 'scp079',
    ),
  ];

  IconData _getAvatarIcon(String avatar) {
    switch (avatar) {
      case 'researcher':
        return Icons.science;
      case 'agent':
        return Icons.shield;
      case 'scp079':
        return Icons.computer;
      default:
        return Icons.person;
    }
  }

  Color _getAvatarColor(String avatar) {
    switch (avatar) {
      case 'researcher':
        return SCPTheme.scpGold;
      case 'agent':
        return SCPTheme.accentRed;
      case 'scp079':
        return const Color(0xFF00FF41); // Matrix green
      default:
        return SCPTheme.textSecondary;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedPersona = ref.watch(selectedPersonaProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('SELECT PERSONA'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Choose your SCP Foundation contact:',
              style: TextStyle(
                fontSize: 14,
                color: SCPTheme.textSecondary,
              ),
            ),
            const SizedBox(height: 24),

            // Persona cards
            Expanded(
              child: ListView.separated(
                itemCount: _personas.length,
                separatorBuilder: (_, __) => const SizedBox(height: 16),
                itemBuilder: (context, index) {
                  final persona = _personas[index];
                  final isSelected = selectedPersona?.id == persona.id;
                  final avatarColor = _getAvatarColor(persona.avatar);

                  return GestureDetector(
                    onTap: () {
                      ref.read(selectedPersonaProvider.notifier).select(persona);
                    },
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: SCPTheme.surfaceCard,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: isSelected
                              ? avatarColor
                              : Colors.transparent,
                          width: 2,
                        ),
                        boxShadow: isSelected
                            ? [
                                BoxShadow(
                                  color: avatarColor.withValues(alpha: 0.2),
                                  blurRadius: 16,
                                  spreadRadius: 2,
                                ),
                              ]
                            : [],
                      ),
                      child: Row(
                        children: [
                          // Avatar
                          Container(
                            width: 56,
                            height: 56,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: avatarColor.withValues(alpha: 0.15),
                              border: Border.all(
                                color: avatarColor.withValues(alpha: 0.5),
                              ),
                            ),
                            child: Icon(
                              _getAvatarIcon(persona.avatar),
                              color: avatarColor,
                              size: 28,
                            ),
                          ),
                          const SizedBox(width: 16),
                          // Info
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Text(
                                      persona.name,
                                      style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.w600,
                                        color: avatarColor,
                                      ),
                                    ),
                                    if (persona.isDefault) ...[
                                      const SizedBox(width: 8),
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 6,
                                          vertical: 2,
                                        ),
                                        decoration: BoxDecoration(
                                          color: SCPTheme.scpGold.withValues(alpha: 0.2),
                                          borderRadius: BorderRadius.circular(4),
                                        ),
                                        child: const Text(
                                          'DEFAULT',
                                          style: TextStyle(
                                            fontSize: 9,
                                            fontWeight: FontWeight.w700,
                                            color: SCPTheme.scpGold,
                                            letterSpacing: 1,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  persona.description,
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: SCPTheme.textSecondary,
                                    height: 1.4,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          // Selection indicator
                          if (isSelected)
                            Icon(Icons.check_circle, color: avatarColor, size: 24),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),

            // Proceed button
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: () {
                  // Default to researcher if none selected
                  if (selectedPersona == null) {
                    ref.read(selectedPersonaProvider.notifier).select(
                        _personas.first);
                  }
                  context.go('/chat');
                },
                child: const Text(
                  'BEGIN BRIEFING',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 2,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
