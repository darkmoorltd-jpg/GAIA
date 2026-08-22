import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import 'diagnose_screen.dart';
import 'buy_scans_screen.dart';
import 'video_scan_screen.dart';
import 'voice_agronomist_screen.dart';
import 'satellite_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0F2027), Color(0xFF203A43), Color(0xFF2C5364)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              // Glowing title
              Padding(
                padding: const EdgeInsets.all(20),
                child: ShaderMask(
                  shaderCallback: (bounds) => const LinearGradient(
                    colors: [Color(0xFF00C853), Color(0xFF69F0AE), Color(0xFF00C853)],
                  ).createShader(bounds),
                  child: const Text(
                    'GAIA',
                    style: TextStyle(
                      fontSize: 45,
                      fontWeight: FontWeight.w900,
                      color: Colors.white,
                      letterSpacing: 6,
                    ),
                  ),
                ),
              ),
              const Text(
                'Global Agricultural Intelligence Assistant',
                style: TextStyle(color: Colors.white70, fontSize: 14),
              ),
              const SizedBox(height: 20),
              // Scan counter card
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 20),
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white.withOpacity(0.15)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.flash_on, color: Color(0xFF00C853), size: 35),
                    const SizedBox(width: 10),
                    Text(
                      '${auth.scanBalance}',
                      style: const TextStyle(
                        fontSize: 40,
                        fontWeight: FontWeight.w900,
                        color: Color(0xFF00C853),
                      ),
                    ),
                    const SizedBox(width: 10),
                    const Text('Scans Remaining', style: TextStyle(color: Colors.white70)),
                  ],
                ),
              ),
              const SizedBox(height: 25),
              // Module grid
              Expanded(
                child: GridView.count(
                  crossAxisCount: 2,
                  padding: const EdgeInsets.all(16),
                  crossAxisSpacing: 15,
                  mainAxisSpacing: 15,
                  children: [
                    _moduleCard(context, 'Crop Disease', Icons.spa, const Color(0xFF4CAF50), () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const DiagnoseScreen()));
                    }),
                    _moduleCard(context, 'Pest Detection', Icons.bug_report, const Color(0xFFFF9800), () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const DiagnoseScreen()));
                    }),
                    _moduleCard(context, 'Soil Analysis', Icons.landscape, const Color(0xFF795548), () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const DiagnoseScreen()));
                    }),
                    _moduleCard(context, 'Livestock', Icons.pets, const Color(0xFF7C4DFF), () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const DiagnoseScreen()));
                    }),
                    _moduleCard(context, 'Video Scan', Icons.videocam, const Color(0xFF00BCD4), () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const VideoScanScreen()));
                    }),
                    _moduleCard(context, 'Voice Agronomist', Icons.mic, const Color(0xFFE91E63), () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const VoiceAgronomistScreen()));
                    }),
                    _moduleCard(context, 'Satellite', Icons.satellite_alt, const Color(0xFF3F51B5), () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const SatelliteScreen()));
                    }),
                    _moduleCard(context, 'Buy Scans', Icons.shopping_cart, const Color(0xFFFFC107), () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const BuyScansScreen()));
                    }),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _moduleCard(BuildContext context, String title, IconData icon, Color color, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.06),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 42, color: color),
            const SizedBox(height: 10),
            Text(title, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }
}
