import 'package:flutter/material.dart';

class MarketplaceScreen extends StatefulWidget {
  const MarketplaceScreen({super.key});

  @override
  State<MarketplaceScreen> createState() => _MarketplaceScreenState();
}

class _MarketplaceScreenState extends State<MarketplaceScreen> {
  final List<Map<String, dynamic>> _listings = [
    {'crop': 'Maize', 'variety': 'SAMMAZ 15', 'price': '₦220,000', 'location': 'Kaduna', 'image': '🌽', 'featured': true, 'organic': true, 'rating': 4.8, 'seller': 'Ibrahim Musa', 'type': 'Verified Farmer'},
    {'crop': 'Rice', 'variety': 'FARO 44', 'price': '₦350,000', 'location': 'Kano', 'image': '🌾', 'featured': true, 'organic': false, 'rating': 4.9, 'seller': 'Aisha Bello', 'type': 'Premium Seller'},
    {'crop': 'Beans', 'variety': 'IT89KD-288', 'price': '₦480,000', 'location': 'Jos', 'image': '🫘', 'featured': false, 'organic': true, 'rating': 4.7, 'seller': 'David Okonkwo', 'type': 'Organic Certified'},
    {'crop': 'Tomatoes', 'variety': 'Roma VF', 'price': '₦180,000', 'location': 'Zaria', 'image': '🍅', 'featured': false, 'organic': false, 'rating': 4.6, 'seller': 'Fatima Yusuf', 'type': 'Verified Farmer'},
    {'crop': 'Yam', 'variety': 'Dioscorea rotundata', 'price': '₦550,000', 'location': 'Makurdi', 'image': '🍠', 'featured': true, 'organic': true, 'rating': 4.9, 'seller': 'John Tarka', 'type': 'Premium Seller'},
    {'crop': 'Cassava', 'variety': 'TME 419', 'price': '₦120,000', 'location': 'Ondo', 'image': '🥔', 'featured': false, 'organic': true, 'rating': 4.6, 'seller': 'Grace Adeyemi', 'type': 'Organic Certified'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 1,
        title: const Text('🌍 GAIA Market', style: TextStyle(color: Color(0xFF2E7D32), fontWeight: FontWeight.bold)),
      ),
      body: Column(
        children: [
          // Search bar
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              decoration: InputDecoration(
                hintText: '🔍 Search crops, varieties, or locations...',
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                prefixIcon: const Icon(Icons.search),
              ),
            ),
          ),
          Expanded(
            child: GridView.builder(
              padding: const EdgeInsets.all(12),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 0.75,
              ),
              itemCount: _listings.length,
              itemBuilder: (context, index) {
                final listing = _listings[index];
                return _listingCard(listing);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _listingCard(Map<String, dynamic> listing) {
    return GestureDetector(
      onTap: () {},
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(15),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 8),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image area
            Expanded(
              child: Stack(
                children: [
                  Container(
                    width: double.infinity,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          listing['organic'] ? const Color(0xFFE8F5E9) : const Color(0xFFF5F5F5),
                          listing['organic'] ? const Color(0xFFC8E6C9) : const Color(0xFFE0E0E0),
                        ],
                      ),
                      borderRadius: const BorderRadius.vertical(top: Radius.circular(15)),
                    ),
                    child: Center(
                      child: Text(listing['image'], style: const TextStyle(fontSize: 40)),
                    ),
                  ),
                  if (listing['featured'])
                    Positioned(
                      top: 8,
                      left: 8,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFF9800),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Text('⭐ Featured', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                      ),
                    ),
                  if (listing['organic'])
                    Positioned(
                      top: 8,
                      right: 8,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFF4CAF50),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Text('🌿', style: TextStyle(fontSize: 12)),
                      ),
                    ),
                ],
              ),
            ),
            // Info area
            Padding(
              padding: const EdgeInsets.all(10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(listing['crop'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  Text('${listing['price']}/tonnes', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15, color: Color(0xFF2E7D32))),
                  const SizedBox(height: 4),
                  Text('📍 ${listing['location']}', style: TextStyle(color: Colors.grey[600], fontSize: 11)),
                  Text('⭐ ${listing['rating']}', style: TextStyle(color: Colors.amber[700], fontSize: 11)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
