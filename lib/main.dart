import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

void main() {
  // TODO: Inicializar Firebase aquí
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ConstruApp',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  File? _image;
  final ImagePicker _picker = ImagePicker();
  final List<Rect> _completedElements = [];

  Future<void> _pickImage() async {
    final XFile? pickedFile = await _picker.pickImage(source: ImageSource.gallery);

    if (pickedFile != null) {
      setState(() {
        _image = File(pickedFile.path);
      });
      _uploadImageToFirebase();
    }
  }

  void _uploadImageToFirebase() {
    // TODO: Implementar la subida de la imagen a Firebase Storage.
    // Esto requerirá configurar las credenciales de Firebase en la app.
    // Por ahora, solo mostraremos un mensaje.
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Plano cargado localmente. Siguiente paso: subir a Firebase.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Gestor de Planos de Construcción'),
      ),
      body: Center(
        child: _image == null
            ? const Text('No hay ningún plano cargado.')
            : Stack(
                fit: StackFit.expand,
                children: [
                  Image.file(_image!, fit: BoxFit.contain),
                  CustomPaint(
                    painter: BlueprintPainter(rects: _completedElements),
                  ),
                ],
              ),
      ),
      floatingActionButton: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          FloatingActionButton(
            onPressed: _pickImage,
            tooltip: 'Cargar Plano',
            child: const Icon(Icons.add_a_photo),
          ),
          const SizedBox(height: 16),
          FloatingActionButton(
            onPressed: () => _showMarkElementDialog(),
            tooltip: 'Marcar Elemento',
            child: const Icon(Icons.edit),
            backgroundColor: Colors.green,
          ),
        ],
      ),
    );
  }

  void _showMarkElementDialog() {
    final TextEditingController axis1Controller = TextEditingController();
    final TextEditingController axis2Controller = TextEditingController();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Marcar Elemento como Montado'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: axis1Controller,
                decoration: const InputDecoration(labelText: 'Eje 1 (ej. A)'),
              ),
              TextField(
                controller: axis2Controller,
                decoration: const InputDecoration(labelText: 'Eje 2 (ej. 3)'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancelar'),
            ),
            ElevatedButton(
              onPressed: () {
                final String axis1 = axis1Controller.text;
                final String axis2 = axis2Controller.text;
                if (axis1.isNotEmpty && axis2.isNotEmpty) {
                  _markElementInFirestore(axis1, axis2);
                  Navigator.of(context).pop();
                }
              },
              child: const Text('Marcar'),
            ),
          ],
        );
      },
    );
  }

  void _markElementInFirestore(String axis1, String axis2) {
    // TODO: Implementar la actualización en Firestore.
    // La lógica real buscaría las coordenadas del elemento 'axis1-axis2'
    // en los datos extraídos por la Cloud Function.
    // Por ahora, añadimos un rectángulo de ejemplo.
    setState(() {
      // Estas coordenadas son de ejemplo y deberán ser dinámicas.
      final double randomX = (axis1.hashCode % 100).toDouble() * 3;
      final double randomY = (axis2.hashCode % 100).toDouble() * 4;
      _completedElements.add(Rect.fromLTWH(randomX, randomY, 50, 80));
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Elemento en Eje $axis1-$axis2 marcado visualmente (simulado).')),
    );
  }
}

class BlueprintPainter extends CustomPainter {
  final List<Rect> rects;

  BlueprintPainter({required this.rects});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.green.withOpacity(0.5)
      ..style = PaintingStyle.fill;

    for (final rect in rects) {
      canvas.drawRect(rect, paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}
