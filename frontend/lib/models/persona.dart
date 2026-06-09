/// Persona character model.
class Persona {
  final String id;
  final String name;
  final String description;
  final String avatar;
  final bool isDefault;

  const Persona({
    required this.id,
    required this.name,
    required this.description,
    required this.avatar,
    this.isDefault = false,
  });
}
