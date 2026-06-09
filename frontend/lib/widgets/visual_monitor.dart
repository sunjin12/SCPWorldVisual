import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/theme.dart';
import '../models/persona.dart';
import '../providers/chat_provider.dart';

/// CRT 모니터 스타일의 CCTV 뷰 위젯.
///
/// Layer 구조:
///   Layer 1: 페르소나별 배경
///   Layer 2: 환경 VFX (Agent 경보 램프)
///   Layer 3: CRT 스캔라인
///   Layer 4: 캐릭터 이미지 (하단 중앙, 글로우 효과)
///   Layer 5: 상단 HUD (CAM ID, LED, 상태)
///   Layer 6: 하단 상태바
class VisualMonitor extends ConsumerStatefulWidget {
  final Persona persona;
  const VisualMonitor({super.key, required this.persona});

  @override
  ConsumerState<VisualMonitor> createState() => _VisualMonitorState();
}

class _VisualMonitorState extends ConsumerState<VisualMonitor>
    with TickerProviderStateMixin {
  late AnimationController _breathingController;
  bool _wasStreaming = false;
  double _glowIntensity = 0.0;
  Timer? _glowTimer;

  @override
  void initState() {
    super.initState();
    _breathingController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _breathingController.dispose();
    _glowTimer?.cancel();
    super.dispose();
  }

  String _statusText({required bool isStreaming, String? stage}) {
    if (isStreaming) {
      return 'STATUS: ${stage?.toUpperCase() ?? "PROCESSING"}...';
    }
    return 'STATUS: CONNECTED. STANDBY.';
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(chatProvider);
    final isStreaming = chatState.isLoading;
    final lastMessage =
        chatState.messages.isNotEmpty ? chatState.messages.last : null;
    final stage = lastMessage?.stage;

    // 글로우 강도 전환
    if (isStreaming && !_wasStreaming) {
      _glowTimer?.cancel();
      setState(() => _glowIntensity = 1.0);
    } else if (!isStreaming && _wasStreaming) {
      _glowTimer?.cancel();
      setState(() => _glowIntensity = 0.5);
      _glowTimer = Timer(const Duration(seconds: 2), () {
        if (mounted) setState(() => _glowIntensity = 0.0);
      });
    }
    _wasStreaming = isStreaming;

    // 페르소나별 테마
    String bgAsset = 'assets/images/backgrounds/research_lab.png';
    String charAsset = 'assets/images/characters/researcher/researcher_standing.png';
    Color themeColor = Colors.cyanAccent;

    if (widget.persona.id == 'agent') {
      bgAsset = 'assets/images/backgrounds/tactical_bunker.png';
      charAsset = 'assets/images/characters/agent/agent_standing.png';
      themeColor = SCPTheme.accentRed;
    } else if (widget.persona.id == 'scp079') {
      bgAsset = 'assets/images/backgrounds/server_chamber.png';
      charAsset = 'assets/images/characters/scp079/scp-079_standing.png';
      themeColor = Colors.greenAccent;
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.black,
          border: Border.all(color: const Color(0xFF2A2A4A), width: 2),
        ),
        child: Stack(
          fit: StackFit.expand,
          children: [
            // Layer 1: 배경 이미지
            Image.asset(
              bgAsset,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => Container(color: Colors.black),
            ),

            // Layer 2: 환경 VFX
            if (widget.persona.id == 'agent')
              AnimatedBuilder(
                animation: _breathingController,
                builder: (context, child) {
                  return Container(
                    decoration: BoxDecoration(
                      gradient: RadialGradient(
                        colors: [
                          themeColor
                              .withOpacity(0.1 * _breathingController.value),
                          Colors.transparent,
                        ],
                      ),
                    ),
                  );
                },
              ),

            // Layer 3: CRT 스캔라인
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: List.generate(
                    100,
                    (index) =>
                        Colors.black.withOpacity(index % 2 == 0 ? 0.06 : 0.0),
                  ),
                ),
              ),
            ),

            // Layer 4: 캐릭터 이미지 (하단 중앙, 글로우)
            Align(
              alignment: Alignment.bottomCenter,
              child: AnimatedBuilder(
                animation: _breathingController,
                builder: (context, _) {
                  return LayoutBuilder(
                    builder: (context, constraints) {
                      // 연구원/요원: 80%, SCP-079: 60%
                      final isMachine = widget.persona.id == 'scp079';
                      final ratio = isMachine ? 0.60 : 0.80;
                      final charHeight = constraints.maxHeight * ratio;
                      final charWidth = charHeight * (isMachine ? 1.12 : 0.72);
                      final idleGlow = 0.08 + _breathingController.value * 0.06;
                      final glow = idleGlow + _glowIntensity * 0.12;
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 16),
                        child: Container(
                          width: charWidth,
                          height: charHeight,
                          decoration: BoxDecoration(
                            gradient: RadialGradient(
                              center: const Alignment(0.0, 0.6),
                              colors: [
                                themeColor.withOpacity(glow),
                                Colors.transparent,
                              ],
                            ),
                          ),
                          child: Image.asset(
                            charAsset,
                            fit: BoxFit.contain,
                            errorBuilder: (_, __, ___) => const SizedBox(),
                          ),
                        ),
                      );
                    },
                  );
                },
              ),
            ),

            // Layer 5: 상단 HUD
            Positioned(
              top: 12,
              left: 12,
              right: 12,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'CAM SEC-ZONE: ${widget.persona.id.toUpperCase()}',
                    style: TextStyle(
                      color: themeColor,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'monospace',
                    ),
                  ),
                  Row(
                    children: [
                      AnimatedBuilder(
                        animation: _breathingController,
                        builder: (context, _) {
                          final ledColor = isStreaming
                              ? Colors.red.withOpacity(
                                  0.5 + 0.5 * _breathingController.value)
                              : Colors.green;
                          return Container(
                            width: 6,
                            height: 6,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: ledColor,
                            ),
                          );
                        },
                      ),
                      const SizedBox(width: 4),
                      Text(
                        isStreaming ? 'TRANSMITTING' : 'MONITORING',
                        style: TextStyle(
                          color: isStreaming ? Colors.red : Colors.green,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Layer 6: 하단 상태바
            Positioned(
              bottom: 12,
              left: 12,
              right: 12,
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                color: Colors.black.withOpacity(0.6),
                child: Text(
                  _statusText(isStreaming: isStreaming, stage: stage),
                  style: TextStyle(
                    color: themeColor,
                    fontSize: 9,
                    fontFamily: 'monospace',
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
