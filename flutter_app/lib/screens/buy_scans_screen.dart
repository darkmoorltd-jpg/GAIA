import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class BuyScansScreen extends StatefulWidget {
  const BuyScansScreen({super.key});

  @override
  State<BuyScansScreen> createState() => _BuyScansScreenState();
}

class _BuyScansScreenState extends State<BuyScansScreen> {
  String _selectedPlan = 'starter';

  final Map<String, Map<String, dynamic>> _plans = {
    'starter': {'name': 'Starter', 'scans': 150, 'price': '₦3,000', 'color': const Color(0xFF4CAF50)},
    'pro': {'name': 'Pro', 'scans': 300, 'price': '₦5,000', 'color': const Color(0xFF2196F3)},
    'business': {'name': 'Business', 'scans': 1000, 'price': '₦10,000', 'color': const Color(0xFFFF9800)},
    'enterprise': {'name': 'Enterprise', 'scans': 5000, 'price': '₦20,000', 'color': const Color(0xFF9C27B0)},
  };

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    return Scaffold(
      backgroundColor: const Color(0xFF0F2027),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Buy Scans', style: TextStyle(color: Colors.white)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Current balance
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [Color(0xFF1B5E20), Color(0xFF4CAF50)]),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                children: [
                  const Text('CURRENT BALANCE', style: TextStyle(color: Colors.white70, fontSize: 12, letterSpacing: 2)),
                  const SizedBox(height: 8),
                  Text('${auth.scanBalance}', style: const TextStyle(fontSize: 48, fontWeight: FontWeight.w900, color: Colors.white)),
                  const Text('scans remaining', style: TextStyle(color: Colors.white70)),
                ],
              ),
            ),
            const SizedBox(height: 25),
            const Text('Choose Your Plan', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 15),
            // Plan cards
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              children: _plans.entries.map((entry) {
                final plan = entry.value;
                final selected = _selectedPlan == entry.key;
                return GestureDetector(
                  onTap: () => setState(() => _selectedPlan = entry.key),
                  child: Container(
                    padding: const EdgeInsets.all(15),
                    decoration: BoxDecoration(
                      color: selected ? plan['color'].withOpacity(0.2) : Colors.white.withOpacity(0.06),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: selected ? plan['color'] : Colors.white.withOpacity(0.15), width: selected ? 2 : 1),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(plan['name'], style: TextStyle(color: plan['color'], fontSize: 16, fontWeight: FontWeight.w700)),
                        const SizedBox(height: 8),
                        Text('${plan['scans']} scans', style: const TextStyle(color: Colors.white70, fontSize: 12)),
                        const SizedBox(height: 5),
                        Text(plan['price'], style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900)),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 25),
            // Pay button
            ElevatedButton(
              onPressed: () {
                // Paystack integration
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Payment integration coming soon')),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00C853),
                foregroundColor: Colors.black,
                minimumSize: const Size(double.infinity, 55),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
              ),
              child: Text('Pay ${_plans[_selectedPlan]!['price']}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            ),
          ],
        ),
      ),
    );
  }
}
