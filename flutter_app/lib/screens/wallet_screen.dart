import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class WalletScreen extends StatelessWidget {
  const WalletScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    return Scaffold(
      backgroundColor: const Color(0xFFE8F5E9),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('💰 My Wallet', style: TextStyle(color: Color(0xFF2E7D32), fontWeight: FontWeight.bold)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Balance card
            Container(
              padding: const EdgeInsets.all(25),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF1B5E20), Color(0xFF4CAF50)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(color: Colors.green.withOpacity(0.3), blurRadius: 15),
                ],
              ),
              child: Column(
                children: [
                  const Text('AVAILABLE BALANCE', style: TextStyle(color: Colors.white70, fontSize: 12, letterSpacing: 2)),
                  const SizedBox(height: 10),
                  const Text('₦0.00', style: TextStyle(fontSize: 42, fontWeight: FontWeight.w900, color: Colors.white)),
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Text('GAIA-XXXX-XXXX-XXXX', style: TextStyle(color: Colors.white70, fontSize: 12)),
                  ),
                  const SizedBox(height: 5),
                  const Text('Wema Bank', style: TextStyle(color: Colors.white70, fontSize: 11)),
                ],
              ),
            ),
            const SizedBox(height: 20),
            // Quick actions
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _actionButton(Icons.add, 'Fund', const Color(0xFF2E7D32)),
                _actionButton(Icons.arrow_upward, 'Send', const Color(0xFF2196F3)),
                _actionButton(Icons.arrow_downward, 'Receive', const Color(0xFFFF9800)),
                _actionButton(Icons.receipt_long, 'History', const Color(0xFF9C27B0)),
              ],
            ),
            const SizedBox(height: 25),
            // Transactions
            const Align(
              alignment: Alignment.centerLeft,
              child: Text('Recent Transactions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF2E7D32))),
            ),
            const SizedBox(height: 10),
            Card(
              child: ListTile(
                leading: const Icon(Icons.receipt, color: Color(0xFF4CAF50)),
                title: const Text('Scan Purchase'),
                subtitle: const Text('Starter Plan - 150 scans'),
                trailing: const Text('₦3,000', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _actionButton(IconData icon, String label, Color color) {
    return Column(
      children: [
        Container(
          width: 55,
          height: 55,
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            borderRadius: BorderRadius.circular(18),
          ),
          child: Icon(icon, color: color, size: 26),
        ),
        const SizedBox(height: 5),
        Text(label, style: const TextStyle(fontSize: 11)),
      ],
    );
  }
}
