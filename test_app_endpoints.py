import unittest
import json
from app import app, state

class FlowMateApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_status_endpoint(self):
        response = self.app.get('/api/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('sensor', data)
        self.assertEqual(data['sensor']['mode'], 'SMARTWATCH')
        self.assertIn('connected', data['sensor'])

    def test_sensor_read_endpoint(self):
        response = self.app.get('/api/sensor/read')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('connected', data)
        self.assertIn('stress', data)

    def test_sensor_measure_endpoint(self):
        response = self.app.post('/api/sensor/measure')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('limitation_note', data)

    def test_hardware_diagnostic_endpoint(self):
        response = self.app.get('/api/hardware/diagnostic')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('diagnostic', data)

if __name__ == '__main__':
    unittest.main()
