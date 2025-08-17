{
    'name': 'AGB Communication Attendance Dashboard',
    'version': '1.0.0',
    'description': 'Employee Attendance Dashboard for AGB Communication Myanmar',
    'author': 'AGB Communication',
    'website': 'https://agbcommunication.com',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_dashboard_templates.xml',
        'views/attendance_dashboard_assets.xml',
        'views/register_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'attendance_dashboard/static/src/css/attendance_dashboard.css',
            'attendance_dashboard/static/src/js/attendance_dashboard.js',
            'attendance_dashboard/static/src/css/register.css',
            'attendance_dashboard/static/src/js/register.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}