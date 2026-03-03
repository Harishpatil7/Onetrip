import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { LayoutDashboard, Users, FileText, Settings, Clock, CheckCircle, LogOut } from 'lucide-react';
import '../index.css';

export default function DashboardLayout() {
    const [appointments, setAppointments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('dashboard'); // Handle switching views
    const navigate = useNavigate();

    const user = JSON.parse(localStorage.getItem('staffUser') || '{}');

    // Verify login on mount
    useEffect(() => {
        if (!localStorage.getItem('staffToken')) {
            navigate('/login');
        } else {
            fetchAppts();
        }
    }, [navigate]);

    const fetchAppts = async () => {
        try {
            // Connect to our SQLite FastAPI backend to fetch real data
            const res = await axios.get('http://localhost:8000/api/dashboard/appointments');
            setAppointments(res.data);
        } catch (e) {
            console.error(e);
            // In case we haven't created data yet or server is off, fallback:
            setAppointments([]);
        } finally {
            setLoading(false);
        }
    };

    const markCompleted = async (id) => {
        try {
            await axios.put(`http://localhost:8000/api/dashboard/appointments/${id}/complete`);
            fetchAppts(); // Refresh data correctly
        } catch (e) {
            console.error(e);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('staffToken');
        localStorage.removeItem('staffUser');
        navigate('/login');
    };

    const pendingCount = appointments.filter(a => a.status === 'PENDING').length;
    const completedCount = appointments.filter(a => a.status === 'COMPLETED').length;
    const totalCount = appointments.length;

    return (
        <div className="dashboard-container">
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="logo">
                    <div style={{ background: 'var(--primary)', color: 'white', padding: '6px', borderRadius: '8px' }}>
                        <span style={{ fontWeight: 800, fontSize: '20px' }}>1</span>
                    </div>
                    OneTrip
                </div>

                <nav style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                    <div
                        className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
                        onClick={() => setActiveTab('dashboard')}
                    >
                        <LayoutDashboard size={20} />
                        Dashboard
                    </div>
                    <div
                        className={`nav-link ${activeTab === 'citizens' ? 'active' : ''}`}
                        onClick={() => setActiveTab('citizens')}
                    >
                        <Users size={20} />
                        Citizens Directory
                    </div>
                    <div
                        className={`nav-link ${activeTab === 'services' ? 'active' : ''}`}
                        onClick={() => setActiveTab('services')}
                    >
                        <FileText size={20} />
                        Services Repo
                    </div>

                    <div style={{ marginTop: 'auto' }}>
                        <div className="nav-link" onClick={handleLogout}>
                            <LogOut size={20} color="#DC2626" />
                            <span style={{ color: '#DC2626' }}>Secure Logout</span>
                        </div>
                        <div className="nav-link">
                            <Settings size={20} />
                            Settings
                        </div>
                    </div>
                </nav>
            </aside>

            {/* Main Content Area */}
            <main className="main-content">
                <div className="header">
                    <div>
                        <h1>{activeTab === 'dashboard' ? 'Staff Dashboard' : activeTab === 'citizens' ? 'Citizens Database' : 'Government Services'}</h1>
                        <p style={{ color: 'var(--text-muted)' }}>Secure authentication confirmed.</p>
                    </div>
                    <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                        <span style={{ fontSize: '14px', fontWeight: 500 }}>{user.office || 'Govt Office #04'} | {user.username}</span>
                        <div style={{ width: '40px', height: '40px', backgroundColor: '#E5E7EB', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                            STAFF
                        </div>
                    </div>
                </div>

                {activeTab === 'dashboard' && (
                    <>
                        {/* Stats Row */}
                        <div className="stats-grid">
                            <div className="stat-card">
                                <div className="stat-icon icon-blue">
                                    <Users size={24} />
                                </div>
                                <div className="stat-info">
                                    <h3>Total Expected Today</h3>
                                    <p>{totalCount}</p>
                                </div>
                            </div>

                            <div className="stat-card">
                                <div className="stat-icon icon-orange">
                                    <Clock size={24} />
                                </div>
                                <div className="stat-info">
                                    <h3>Waiting / Pending</h3>
                                    <p>{pendingCount}</p>
                                </div>
                            </div>

                            <div className="stat-card">
                                <div className="stat-icon icon-green">
                                    <CheckCircle size={24} />
                                </div>
                                <div className="stat-info">
                                    <h3>Completed Visits</h3>
                                    <p>{completedCount}</p>
                                </div>
                            </div>
                        </div>

                        {/* Action Table */}
                        <div className="table-card">
                            <div className="table-header">
                                <h2>Today's Secure Tokens</h2>
                                <button onClick={fetchAppts} className="action-btn" style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: 'white', color: 'var(--text-main)', border: '1px solid var(--border)' }}>
                                    Refresh Live Data
                                </button>
                            </div>

                            <table style={{ width: '100%' }}>
                                <thead>
                                    <tr>
                                        <th>Citizen Info</th>
                                        <th>Location</th>
                                        <th>Requested Service</th>
                                        <th>Live Token</th>
                                        <th>Status</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {appointments.length === 0 ? (
                                        <tr>
                                            <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                                                No appointments currently generated in the database.
                                            </td>
                                        </tr>
                                    ) : appointments.map((app) => (
                                        <tr key={app.id}>
                                            <td>
                                                <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{app.name}</div>
                                                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{app.lang === 'KN' ? 'Kannada' : 'English'}</div>
                                            </td>
                                            <td style={{ color: 'var(--text-muted)' }}>{app.location}</td>
                                            <td style={{ fontWeight: 500 }}>{app.service}</td>
                                            <td>
                                                <span className="token-badge">{app.token}</span>
                                                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>{app.time}</div>
                                            </td>
                                            <td>
                                                <span className={`status-badge ${app.status === 'PENDING' ? 'status-pending' : 'status-completed'}`}>
                                                    {app.status}
                                                </span>
                                            </td>
                                            <td>
                                                {app.status === 'PENDING' ? (
                                                    <button
                                                        className="action-btn"
                                                        onClick={() => markCompleted(app.id)}
                                                    >
                                                        Verify & Complete
                                                    </button>
                                                ) : (
                                                    <button className="action-btn" disabled>
                                                        Resolved ✓
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                )}

                {/* MOCK Citizens Page */}
                {activeTab === 'citizens' && (
                    <div className="table-card" style={{ padding: '24px' }}>
                        <h2>Citizens Database Directory</h2>
                        <p style={{ color: 'var(--text-muted)' }}>The government securely stores registered citizens.</p>
                        <br />
                        <div style={{ padding: '20px', border: '1px solid var(--border)', borderRadius: '8px', backgroundColor: '#F9FAFB' }}>
                            <p><strong>System Message:</strong> 4 Citizens currently registered in the database memory.</p>
                        </div>
                    </div>
                )}

                {/* MOCK Services Repo */}
                {activeTab === 'services' && (
                    <div className="table-card" style={{ padding: '24px' }}>
                        <h2>Active Government Services</h2>
                        <p style={{ color: 'var(--text-muted)' }}>Currently supported by OneTrip algorithm.</p>
                        <ul style={{ padding: '20px' }}>
                            <li><strong>Income Certificate</strong> (ಆದಾಯ ಪ್ರಮಾಣಪತ್ರ)</li>
                            <li><strong>Ration Card</strong> (ಪಡಿತರ ಚೀಟಿ)</li>
                        </ul>
                    </div>
                )}
            </main>
        </div>
    );
}
