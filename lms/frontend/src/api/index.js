import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear auth and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.clear();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// ─── Auth API calls ───────────────────────────────────────────────────────────

export const authAPI = {
  studentRegister: (data) => api.post('/auth/student/register/', data),
  studentLogin: (data) => api.post('/auth/student/login/', data),
  facultyLogin: (data) => api.post('/auth/faculty/login/', data),
  adminLogin: (data) => api.post('/auth/admin/login/', data),
  forgotPassword: (data) => api.post('/auth/forgot-password/', data),
  resetPassword: (data) => api.post('/auth/reset-password/', data),
  changePassword: (data) => api.post('/auth/change-password/', data),
};

// ─── Student API calls ────────────────────────────────────────────────────────

export const studentAPI = {
  getProfile: () => api.get('/student/profile/'),
  updateProfile: (data) => api.put('/student/profile/', data),
  getEnrollments: () => api.get('/courses/enrollments/'),
  enroll: (data) => api.post('/courses/enrollments/', data),
  dropCourse: (id) => api.delete(`/courses/enrollments/${id}/`),
  getAttendance: (params) => api.get('/attendance/my/', { params }),
  getMarks: (params) => api.get('/marks/my/', { params }),
  getFees: () => api.get('/fees/my/'),
  payFees: (data) => api.post('/fees/pay/', data),
  getReceipt: (receiptNumber) => api.get(`/fees/receipt/${receiptNumber}/`),
  getAnnouncements: () => api.get('/announcements/'),
};

// ─── Faculty API calls ────────────────────────────────────────────────────────

export const facultyAPI = {
  getProfile: () => api.get('/faculty/profile/'),
  getMyCourses: () => api.get('/courses/my-courses/'),
  getCourseAttendance: (courseId, params) => api.get(`/attendance/course/${courseId}/`, { params }),
  markAttendance: (data) => api.post('/attendance/mark/', data),
  getCourseMarks: (courseId) => api.get(`/marks/course/${courseId}/`),
  enterMarks: (courseId, data) => api.post(`/marks/course/${courseId}/enter/`, data),
  getAnnouncements: () => api.get('/announcements/'),
};

// ─── Admin API calls ──────────────────────────────────────────────────────────

export const adminAPI = {
  getDashboard: () => api.get('/admin/dashboard/'),
  getStudents: (params) => api.get('/admin/students/', { params }),
  getStudent: (id) => api.get(`/admin/students/${id}/`),
  updateStudent: (id, data) => api.put(`/admin/students/${id}/`, data),
  deactivateStudent: (id) => api.delete(`/admin/students/${id}/`),
  getFaculty: (params) => api.get('/admin/faculty/', { params }),
  registerFaculty: (data) => api.post('/auth/faculty/register/', data),
  getFeeReport: () => api.get('/fees/admin/report/'),
  getSubjects: (params) => api.get('/courses/subjects/', { params }),
  createSubject: (data) => api.post('/courses/subjects/', data),
  getCourses: (params) => api.get('/courses/', { params }),
  createCourse: (data) => api.post('/courses/', data),
  createFeeStructure: (data) => api.post('/fees/structures/', data),
  getFeeStructures: () => api.get('/fees/structures/'),
  createAnnouncement: (data) => api.post('/announcements/', data),
  getAnnouncements: () => api.get('/announcements/'),
};