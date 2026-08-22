import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'https://api.gaia.ai/v1';

  // Auth
  Future<Map<String, dynamic>> signup(String email, String password, String firstName, String lastName, String phone) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/signup'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'first_name': firstName,
        'last_name': lastName,
        'phone': phone,
      }),
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> googleAuth() async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/google'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'provider': 'google'}),
    );
    return jsonDecode(response.body);
  }

  // Diagnosis
  Future<Map<String, dynamic>> diagnoseCrop(String crop, File image) async {
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/diagnose/crop'));
    request.fields['crop'] = crop;
    request.files.add(await http.MultipartFile.fromPath('file', image.path));
    final response = await request.send();
    return jsonDecode(await response.stream.bytesToString());
  }

  Future<Map<String, dynamic>> diagnosePest(File image) async {
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/diagnose/pest'));
    request.files.add(await http.MultipartFile.fromPath('file', image.path));
    final response = await request.send();
    return jsonDecode(await response.stream.bytesToString());
  }

  Future<Map<String, dynamic>> diagnoseSoil(File image) async {
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/diagnose/soil'));
    request.files.add(await http.MultipartFile.fromPath('file', image.path));
    final response = await request.send();
    return jsonDecode(await response.stream.bytesToString());
  }

  Future<Map<String, dynamic>> diagnoseLivestock(String animal, File image) async {
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/diagnose/livestock'));
    request.fields['animal'] = animal;
    request.files.add(await http.MultipartFile.fromPath('file', image.path));
    final response = await request.send();
    return jsonDecode(await response.stream.bytesToString());
  }

  // Scans
  Future<int> getScanBalance(String userId) async {
    final response = await http.get(Uri.parse('$baseUrl/scans/balance/$userId'));
    final data = jsonDecode(response.body);
    return data['remaining'] ?? 0;
  }

  Future<bool> deductScan(String userId, int amount) async {
    final response = await http.post(
      Uri.parse('$baseUrl/scans/deduct'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'user_id': userId, 'amount': amount}),
    );
    return response.statusCode == 200;
  }

  // Payments
  Future<Map<String, dynamic>> initializePayment(String email, int amount, String plan) async {
    final response = await http.post(
      Uri.parse('$baseUrl/payments/initialize'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'amount': amount, 'plan': plan}),
    );
    return jsonDecode(response.body);
  }
}
