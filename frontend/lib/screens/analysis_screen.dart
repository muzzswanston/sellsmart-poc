// frontend/lib/screens/analysis_screen.dart
import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class AnalysisScreen extends StatefulWidget {
  final String imagePath;
  const AnalysisScreen({Key? key, required this.imagePath}) : super(key: key);

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  bool _loading = true;
  Map<String, dynamic> _result = {};

  @override
  void initState() {
    super.initState();
    _analyzeImage();
  }

  Future<void> _analyzeImage() async {
    setState(() => _loading = true);

    var uri = Uri.parse('https://YOUR_BACKEND_URL_HERE/analyze'); // ← CHANGE THIS
    var request = http.MultipartRequest('POST', uri);
    request.files.add(await http.MultipartFile.fromPath('image', widget.imagePath));

    try {
      var response = await request.send().timeout(const Duration(seconds: 30));
      if (response.statusCode == 200) {
        var respStr = await response.stream.bytesToString();
        setState(() {
          _result = json.decode(respStr);
          _loading = false;
        });
      } else {
        setState(() {
          _result = {"error": "Server error ${response.statusCode}"};
          _loading = false;
        });
      }
    } catch (e) {
      setState(() {
        _result = {"error": "Network error: $e"};
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI Analysis Result')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _result.containsKey('error')
                ? Center(child: Text('Error: ${_result['error']}', style: const TextStyle(color: Colors.red)))
                : SingleChildScrollView(
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Image.file(File(widget.imagePath), height: 300, fit: BoxFit.cover),
                            const SizedBox(height: 20),
                            Text(
                              'Item: ${_result['data']?['item_name'] ?? 'Unknown'}',
                              style: Theme.of(context).textTheme.headlineSmall,
                            ),
                            const SizedBox(height: 30),
                            const Text('Full JSON Response:', style: TextStyle(fontWeight: FontWeight.bold)),
                            const SizedBox(height: 10),
                            SelectableText(
                              const JsonEncoder.withIndent('  ').convert(_result), // ← FIXED: pretty print
                              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
      ),
    );
  }
}
