import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// SCP Foundation-inspired dark theme.
class SCPTheme {
  SCPTheme._();

  // Core colors
  static const primaryBlack = Color(0xFF0D0D0D);
  static const surfaceDark = Color(0xFF1A1A2E);
  static const surfaceCard = Color(0xFF16213E);
  static const accentRed = Color(0xFFE94560);
  static const scpGold = Color(0xFFD4AF37);
  static const textPrimary = Color(0xFFE8E8E8);
  static const textSecondary = Color(0xFF9E9E9E);
  static const redactedBlack = Color(0xFF000000);
  static const successGreen = Color(0xFF4CAF50);
  static const warningAmber = Color(0xFFFF9800);

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: primaryBlack,
      colorScheme: const ColorScheme.dark(
        primary: accentRed,
        secondary: scpGold,
        surface: surfaceDark,
        onSurface: textPrimary,
        error: accentRed,
      ),
      textTheme: GoogleFonts.notoSansKrTextTheme(
        ThemeData.dark().textTheme,
      ).apply(
        bodyColor: textPrimary,
        displayColor: textPrimary,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: surfaceDark,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.robotoMono(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: scpGold,
          letterSpacing: 2.0,
        ),
      ),
      cardTheme: const CardThemeData(
        color: surfaceCard,
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(12)),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: accentRed,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceCard,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: accentRed, width: 1.5),
        ),
        hintStyle: const TextStyle(color: textSecondary),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 20,
          vertical: 16,
        ),
      ),
      dividerTheme: const DividerThemeData(
        color: Color(0xFF2A2A4A),
        thickness: 1,
      ),
    );
  }
}
