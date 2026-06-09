import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/persona.dart';

/// Selected persona state.
final selectedPersonaProvider = NotifierProvider<SelectedPersonaNotifier, Persona?>(
  SelectedPersonaNotifier.new,
);

class SelectedPersonaNotifier extends Notifier<Persona?> {
  @override
  Persona? build() => null;

  void select(Persona persona) {
    state = persona;
  }
}
