import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'screens/home_screen.dart';

List<CameraDescription> cameras = [];

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  cameras = await availableCameras();
  runApp(const SellSmartPOCApp());
}

class SellSmartPOCApp extends StatelessWidget {
  const SellSmartPOCApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SellSmart POC',
      theme: ThemeData(
        primarySwatch: Colors.green,
        useMaterial3: true,
      ),
      home: HomeScreen(cameras: cameras),
      debugShowCheckedModeBanner: false,
    );
  }
}
