import 'package:flutter/material.dart';
import '../config/theme.dart';

/// CC-BY-SA 3.0 license footer — REQUIRED per constraint #6.
class SCPFooter extends StatelessWidget {
  const SCPFooter({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      decoration: const BoxDecoration(
        color: SCPTheme.primaryBlack,
        border: Border(
          top: BorderSide(color: Color(0xFF2A2A4A), width: 0.5),
        ),
      ),
      child: const Text(
        'Content based on the SCP Foundation Wiki — CC-BY-SA 3.0 License',
        textAlign: TextAlign.center,
        style: TextStyle(
          fontSize: 10,
          color: SCPTheme.textSecondary,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}
