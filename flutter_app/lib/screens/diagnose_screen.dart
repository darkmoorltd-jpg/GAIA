import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';

class DiagnoseScreen extends StatefulWidget {
  const DiagnoseScreen({super.key});

  @override
  State<DiagnoseScreen> createState() => _DiagnoseScreenState();
}

class _DiagnoseScreenState extends State<DiagnoseScreen> {
  String _selectedType = 'Crop';
  File? _image;
  bool _isLoading = false;
  String _result = '';
  double _confidence = 0;

  final List<String> _types = ['Crop', 'Pest', 'Soil', 'Livestock'];
  final List<String> _crops = ['Maize', 'Rice', 'Beans', 'Potato', 'Wheat', 'Millet', 'Soybean', 'Pepper', 'Cabbage'];

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked != null) {
      setState(() {
        _image = File(picked.path);
        _result = '';
      });
    }
  }

  Future<void> _captureImage() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.camera);
    if (picked != null) {
      setState(() {
        _image = File(picked.path);
        _result = '';
      });
    }
  }

  Future<void> _analyze() async {
    if (_image == null) return;
    setState(() {
      _isLoading = true;
      _result = '';
    });
    // Simulate analysis
    await Future.delayed(const Duration(seconds: 2));
    setState(() {
      _isLoading = false;
      _result = _selectedType == 'Crop' ? 'Northern Leaf Blight' : _selectedType == 'Pest' ? 'Fall Armyworm' : _selectedType == 'Soil' ? 'Loamy Soil' : 'Healthy';
      _confidence = 95.5;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F2027),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Diagnose', style: TextStyle(color: Colors.white)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Type selector
            Container(
              height: 50,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: _types.length,
                itemBuilder: (context, index) {
                  final selected = _selectedType == _types[index];
                  return GestureDetector(
                    onTap: () => setState(() => _selectedType = _types[index]),
                    child: Container(
                      margin: const EdgeInsets.only(right: 10),
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      decoration: BoxDecoration(
                        color: selected ? const Color(0xFF00C853) : Colors.white.withOpacity(0.08),
                        borderRadius: BorderRadius.circular(25),
                        border: Border.all(color: selected ? const Color(0xFF00C853) : Colors.white.withOpacity(0.2)),
                      ),
                      child: Text(_types[index], style: TextStyle(color: selected ? Colors.black : Colors.white70, fontWeight: FontWeight.w600)),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 20),
            // Crop selector if crop type
            if (_selectedType == 'Crop') ...[
              const Text('Select Crop', style: TextStyle(color: Colors.white70, fontSize: 14)),
              const SizedBox(height: 10),
              Container(
                height: 40,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: _crops.length,
                  itemBuilder: (context, index) {
                    return Container(
                      margin: const EdgeInsets.only(right: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.06),
                        borderRadius: BorderRadius.circular(15),
                      ),
                      child: Text(_crops[index], style: const TextStyle(color: Colors.white70)),
                    );
                  },
                ),
              ),
            ],
            const SizedBox(height: 20),
            // Image picker
            GestureDetector(
              onTap: _pickImage,
              child: Container(
                height: 200,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white.withOpacity(0.2), style: BorderStyle.solid),
                ),
                child: _image != null
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(20),
                        child: Image.file(_image!, fit: BoxFit.cover),
                      )
                    : const Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.add_a_photo, size: 50, color: Colors.white38),
                          SizedBox(height: 10),
                          Text('Tap to upload image', style: TextStyle(color: Colors.white54)),
                        ],
                      ),
              ),
            ),
            const SizedBox(height: 20),
            // Action buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _captureImage,
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Camera'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white.withOpacity(0.1),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 15),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isLoading ? null : _analyze,
                    icon: _isLoading
                        ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : const Icon(Icons.auto_awesome),
                    label: const Text('Analyze'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00C853),
                      foregroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(vertical: 15),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            // Result card
            if (_result.isNotEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: const Color(0xFF00C853).withOpacity(0.4)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_result, style: const TextStyle(color: Color(0xFF69F0AE), fontSize: 24, fontWeight: FontWeight.w900)),
                    const SizedBox(height: 8),
                    Text('Confidence: ${_confidence.toStringAsFixed(1)}%', style: const TextStyle(color: Colors.white70)),
                    const SizedBox(height: 10),
                    LinearProgressIndicator(
                      value: _confidence / 100,
                      backgroundColor: Colors.white.withOpacity(0.1),
                      color: const Color(0xFF00C853),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
