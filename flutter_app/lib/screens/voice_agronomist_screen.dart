import 'package:flutter/material.dart';

class VoiceAgronomistScreen extends StatefulWidget {
  const VoiceAgronomistScreen({super.key});

  @override
  State<VoiceAgronomistScreen> createState() => _VoiceAgronomistScreenState();
}

class _VoiceAgronomistScreenState extends State<VoiceAgronomistScreen> {
  final TextEditingController _questionController = TextEditingController();
  final List<Map<String, String>> _conversation = [];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A0F2E),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('Voice Agronomist', style: TextStyle(color: Colors.white)),
      ),
      body: Column(
        children: [
          // Dancing tomato
          const Text('🍅', style: TextStyle(fontSize: 60)),
          const Text('GAIA Chat & Voice', style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w900)),
          const SizedBox(height: 20),
          // Conversation
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _conversation.length,
              itemBuilder: (context, index) {
                final msg = _conversation[index];
                final isUser = msg['type'] == 'user';
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 5),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isUser ? Colors.white.withOpacity(0.1) : Colors.white.withOpacity(0.05),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(msg['text']!, style: const TextStyle(color: Colors.white)),
                  ),
                );
              },
            ),
          ),
          // Input area
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _questionController,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: 'Ask anything about your farm...',
                      hintStyle: const TextStyle(color: Colors.white38),
                      filled: true,
                      fillColor: Colors.white.withOpacity(0.06),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(15),
                        borderSide: BorderSide.none,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                ElevatedButton(
                  onPressed: () {
                    final question = _questionController.text.trim();
                    if (question.isNotEmpty) {
                      setState(() {
                        _conversation.add({'type': 'user', 'text': question});
                        _conversation.add({'type': 'gaia', 'text': 'Let me help you with that. What specific issue are you facing?'});
                        _questionController.clear();
                      });
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF7C4DFF),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                  ),
                  child: const Icon(Icons.send),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
