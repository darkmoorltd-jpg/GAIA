import 'package:flutter/material.dart';
import 'dart:async';
import 'login_screen.dart';
import 'home_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    Timer(const Duration(seconds: 3), () {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0F2027), Color(0xFF2C5364)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('GAIA', style: TextStyle(fontSize: 60, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 5)),
              SizedBox(height: 20),
              Text('Agricultural Intelligence', style: TextStyle(color: Colors.white70, fontSize: 16)),
              SizedBox(height: 40),
              CircularProgressIndicator(color: Colors.green),
            ],
          ),
        ),
      ),
    );
  }
}
