import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  String? _userId;
  String? _email;
  int _scanBalance = 30;
  bool _isLoggedIn = false;

  String? get userId => _userId;
  String? get email => _email;
  int get scanBalance => _scanBalance;
  bool get isLoggedIn => _isLoggedIn;

  Future<bool> login(String email, String password) async {
    final api = ApiService();
    final result = await api.login(email, password);
    if (result['success'] == true) {
      _userId = result['user']['id'];
      _email = result['user']['email'];
      _isLoggedIn = true;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('user_id', _userId!);
      await prefs.setString('email', _email!);
      notifyListeners();
      return true;
    }
    return false;
  }

  Future<bool> signup(String email, String password, String firstName, String lastName, String phone) async {
    final api = ApiService();
    final result = await api.signup(email, password, firstName, lastName, phone);
    if (result['success'] == true) {
      _userId = result['user']['id'];
      _email = result['user']['email'];
      _scanBalance = 30;
      _isLoggedIn = true;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('user_id', _userId!);
      await prefs.setString('email', _email!);
      notifyListeners();
      return true;
    }
    return false;
  }

  Future<void> logout() async {
    _userId = null;
    _email = null;
    _isLoggedIn = false;
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    notifyListeners();
  }

  Future<void> refreshScanBalance() async {
    if (_userId != null) {
      final api = ApiService();
      _scanBalance = await api.getScanBalance(_userId!);
      notifyListeners();
    }
  }

  Future<bool> deductScan() async {
    if (_userId != null && _scanBalance > 0) {
      final api = ApiService();
      final success = await api.deductScan(_userId!, 1);
      if (success) {
        _scanBalance--;
        notifyListeners();
        return true;
      }
    }
    return false;
  }
}
