import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    return Scaffold(
      backgroundColor: const Color(0xFFE8F5E9),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('👤 My Profile', style: TextStyle(color: Color(0xFF2E7D32), fontWeight: FontWeight.bold)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Avatar
            CircleAvatar(
              radius: 50,
              backgroundColor: const Color(0xFF2E7D32),
              child: Text(
                auth.email?.substring(0, 1).toUpperCase() ?? 'F',
                style: const TextStyle(fontSize: 35, color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 10),
            Text(auth.email ?? 'Farmer', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 5),
            Text('Plan: Free', style: TextStyle(color: Colors.grey[600])),
            const SizedBox(height: 20),
            // Menu items
            _menuItem('Verify Farmer', Icons.verified_user, const Color(0xFF2E7D32)),
            _menuItem('Payment History', Icons.receipt, const Color(0xFF2196F3)),
            _menuItem('Badges', Icons.emoji_events, const Color(0xFFFF9800)),
            _menuItem('Insurance', Icons.shield, const Color(0xFF9C27B0)),
            _menuItem('Help & Support', Icons.help, const Color(0xFF607D8B)),
            _menuItem('Settings', Icons.settings, const Color(0xFF795548)),
            const SizedBox(height: 20),
            // Logout
            ElevatedButton(
              onPressed: () => auth.logout(),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFC62828),
                foregroundColor: Colors.white,
                minimumSize: const Size(double.infinity, 50),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text('Logout'),
            ),
            const SizedBox(height: 20),
            const Text('Powered by Darkmoor Ltd', style: TextStyle(color: Colors.grey, fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _menuItem(String title, IconData icon, Color color) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 5),
      child: ListTile(
        leading: Icon(icon, color: color),
        title: Text(title),
        trailing: const Icon(Icons.chevron_right),
      ),
    );
  }
}
