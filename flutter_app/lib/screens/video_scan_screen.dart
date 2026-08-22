import 'package:flutter/material.dart';

class VideoScanScreen extends StatefulWidget {
  const VideoScanScreen({super.key});

  @override
  State<VideoScanScreen> createState() => _VideoScanScreenState();
}

class _VideoScanScreenState extends State<VideoScanScreen> {
  String _scanType = 'Crop Disease';
  String _crop = 'Maize';
  bool _isAnalyzing = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F2027),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Video Field Scanner', style: TextStyle(color: Colors.white)),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Scan type
            Container(
              height: 45,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: [
                  _typeChip('Crop Disease', _scanType == 'Crop Disease'),
                  _typeChip('Soil Analysis', _scanType == 'Soil Analysis'),
                ],
              ),
            ),
            const SizedBox(height: 15),
            if (_scanType == 'Crop Disease') ...[
              const Text('Select Crop', style: TextStyle(color: Colors.white70)),
              const SizedBox(height: 8),
              Container(
                height: 40,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children: ['Maize', 'Rice', 'Beans', 'Wheat', 'Millet', 'Soybean', 'Pepper', 'Cabbage']
                      .map((crop) => Padding(
                            padding: const EdgeInsets.only(right: 8),
                            child: GestureDetector(
                              onTap: () => setState(() => _crop = crop),
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 8),
                                decoration: BoxDecoration(
                                  color: _crop == crop ? const Color(0xFF00C853).withOpacity(0.2) : Colors.white.withOpacity(0.06),
                                  borderRadius: BorderRadius.circular(15),
                                  border: Border.all(color: _crop == crop ? const Color(0xFF00C853) : Colors.white.withOpacity(0.15)),
                                ),
                                child: Text(crop, style: TextStyle(color: _crop == crop ? const Color(0xFF69F0AE) : Colors.white70)),
                              ),
                            ),
                          ))
                      .toList(),
                ),
              ),
            ],
            const SizedBox(height: 20),
            // Video placeholder
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white.withOpacity(0.2)),
                ),
                child: const Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.videocam, size: 60, color: Colors.white38),
                    SizedBox(height: 15),
                    Text('Record a video walking through your field', style: TextStyle(color: Colors.white54)),
                    Text('10-30 seconds recommended', style: TextStyle(color: Colors.white38, fontSize: 12)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _isAnalyzing ? null : () {
                setState(() => _isAnalyzing = true);
                Future.delayed(const Duration(seconds: 3), () {
                  setState(() => _isAnalyzing = false);
                });
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00C853),
                foregroundColor: Colors.black,
                minimumSize: const Size(double.infinity, 55),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
              ),
              child: _isAnalyzing
                  ? const CircularProgressIndicator(color: Colors.black)
                  : const Text('Start Video Scan', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _typeChip(String title, bool selected) {
    return Padding(
      padding: const EdgeInsets.only(right: 10),
      child: GestureDetector(
        onTap: () => setState(() => _scanType = title),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          decoration: BoxDecoration(
            color: selected ? const Color(0xFF00C853).withOpacity(0.2) : Colors.white.withOpacity(0.06),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: selected ? const Color(0xFF00C853) : Colors.white.withOpacity(0.15)),
          ),
          child: Text(title, style: TextStyle(color: selected ? const Color(0xFF69F0AE) : Colors.white70, fontWeight: FontWeight.w600)),
        ),
      ),
    );
  }
}
