import 'package:flutter/material.dart';

class SatelliteScreen extends StatefulWidget {
  const SatelliteScreen({super.key});

  @override
  State<SatelliteScreen> createState() => _SatelliteScreenState();
}

class _SatelliteScreenState extends State<SatelliteScreen> {
  String _layer = 'TRUE_COLOR';
  double _lat = 9.0765;
  double _lon = 7.3986;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Satellite Monitor', style: TextStyle(color: Colors.white)),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Farm Location', style: TextStyle(color: Colors.white70)),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    decoration: InputDecoration(
                      labelText: 'Latitude',
                      labelStyle: const TextStyle(color: Colors.white54),
                      filled: true,
                      fillColor: Colors.white.withOpacity(0.06),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                    ),
                    onChanged: (value) => _lat = double.tryParse(value) ?? _lat,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: TextField(
                    decoration: InputDecoration(
                      labelText: 'Longitude',
                      labelStyle: const TextStyle(color: Colors.white54),
                      filled: true,
                      fillColor: Colors.white.withOpacity(0.06),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                    ),
                    onChanged: (value) => _lon = double.tryParse(value) ?? _lon,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 15),
            const Text('Analysis Type', style: TextStyle(color: Colors.white70)),
            const SizedBox(height: 10),
            Container(
              height: 40,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: ['TRUE_COLOR', 'NDVI', 'MOISTURE'].map((layer) {
                  final selected = _layer == layer;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: GestureDetector(
                      onTap: () => setState(() => _layer = layer),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 8),
                        decoration: BoxDecoration(
                          color: selected ? const Color(0xFF3F51B5).withOpacity(0.2) : Colors.white.withOpacity(0.06),
                          borderRadius: BorderRadius.circular(15),
                          border: Border.all(color: selected ? const Color(0xFF818CF8) : Colors.white.withOpacity(0.15)),
                        ),
                        child: Text(layer, style: TextStyle(color: selected ? const Color(0xFFC7D2FE) : Colors.white70, fontSize: 12)),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 20),
            // Satellite image placeholder
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.04),
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: Colors.white.withOpacity(0.15)),
                ),
                child: const Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.satellite_alt, size: 70, color: Colors.white24),
                    SizedBox(height: 15),
                    Text('Satellite imagery will appear here', style: TextStyle(color: Colors.white38)),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
