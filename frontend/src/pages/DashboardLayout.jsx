import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import API_BASE from '../api';
import { LayoutDashboard, Users, FileText, Settings, Clock, CheckCircle, LogOut } from 'lucide-react';
import '../index.css';

export default function DashboardLayout() {
    const [appointments, setAppointments] = useState([]);
    const [citizens, setCitizens] = useState([]);
    const [services, setServices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [citizensLoading, setCitizensLoading] = useState(false);
    const [servicesLoading, setServicesLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('dashboard'); // Handle switching views
    const navigate = useNavigate();

    const user = JSON.parse(localStorage.getItem('staffUser') || '{}');

    // Verify login on mount and tab switch
    useEffect(() => {
        if (!localStorage.getItem('staffToken')) {
            navigate('/login');
        } else {
            if (activeTab === 'dashboard') {
                fetchAppts();
            } else if (activeTab === 'citizens') {
                fetchCitizens();
            } else if (activeTab === 'services') {
                fetchServices();
            }
        }
    }, [navigate, activeTab]);

    const fetchAppts = async () => {
        try {
            const token = localStorage.getItem('staffToken');
            const res = await axios.get(`${API_BASE}/api/dashboard/appointments`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setAppointments(res.data);
        } catch (e) {
            console.error(e);
            if (e.response && e.response.status === 401) {
                handleLogout();
            }
            setAppointments([]);
        } finally {
            setLoading(false);
        }
    };

    const fetchCitizens = async () => {
        setCitizensLoading(true);
        try {
            const token = localStorage.getItem('staffToken');
            const res = await axios.get(`${API_BASE}/api/dashboard/citizens`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setCitizens(res.data);
        } catch (e) {
            console.error(e);
            if (e.response && e.response.status === 401) {
                handleLogout();
            }
            setCitizens([]);
        } finally {
            setCitizensLoading(false);
        }
    };

    const fetchServices = async () => {
        setServicesLoading(true);
        try {
            const token = localStorage.getItem('staffToken');
            const res = await axios.get(`${API_BASE}/api/dashboard/services`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setServices(res.data);
        } catch (e) {
            console.error(e);
            if (e.response && e.response.status === 401) {
                handleLogout();
            }
            setServices([]);
        } finally {
            setServicesLoading(false);
        }
    };

    const markCompleted = async (id) => {
        try {
            const token = localStorage.getItem('staffToken');
            await axios.put(`${API_BASE}/api/dashboard/appointments/${id}/complete`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            fetchAppts(); // Refresh data correctly
        } catch (e) {
            console.error(e);
            if (e.response && e.response.status === 401) {
                handleLogout();
            }
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
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                            <span style={{ fontSize: '14px', fontWeight: 600 }}>{user.username}</span>
                            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{user.role} | {user.office || 'Govt Office'}</span>
                        </div>
                        <div style={{ 
                            padding: '6px 12px', 
                            backgroundColor: user.role === 'Viewer' ? '#FEF3C7' : user.role === 'Officer' ? '#DBEAFE' : '#D1FAE5', 
                            color: user.role === 'Viewer' ? '#D97706' : user.role === 'Officer' ? '#2563EB' : '#059669', 
                            borderRadius: '20px', 
                            fontSize: '12px', 
                            fontWeight: 700 
                        }}>
                            {user.role?.toUpperCase() || 'STAFF'}
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
                                                    user.role === 'Viewer' ? (
                                                        <button className="action-btn" style={{ opacity: 0.5, cursor: 'not-allowed', backgroundColor: '#E5E7EB', color: '#9CA3AF' }} disabled title="Viewers cannot resolve tokens">
                                                            Read-Only
                                                        </button>
                                                    ) : (
                                                        <button
                                                            className="action-btn"
                                                            onClick={() => markCompleted(app.id)}
                                                        >
                                                            Verify & Complete
                                                        </button>
                                                    )
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

                {/* Citizens Page */}
                {activeTab === 'citizens' && (
                    <div className="table-card">
                        <div className="table-header">
                            <div>
                                <h2>Citizens Database Directory</h2>
                                <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '4px' }}>Secure storage of all citizens registered in bot system.</p>
                            </div>
                            <button onClick={fetchCitizens} className="action-btn" style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: 'white', color: 'var(--text-main)', border: '1px solid var(--border)' }}>
                                Refresh Citizens
                            </button>
                        </div>

                        {citizensLoading ? (
                            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading citizens list...</div>
                        ) : (
                            <table style={{ width: '100%' }}>
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Phone Number</th>
                                        <th>Location</th>
                                        <th>Bot State</th>
                                        <th>Language</th>
                                        <th>Selected Service</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {citizens.length === 0 ? (
                                        <tr>
                                            <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                                                No citizens registered in the database yet.
                                            </td>
                                        </tr>
                                    ) : citizens.map((citizen) => (
                                        <tr key={citizen.id}>
                                            <td style={{ fontWeight: 600 }}>{citizen.name || "N/A"}</td>
                                            <td>{citizen.phone_number}</td>
                                            <td style={{ color: 'var(--text-muted)' }}>{citizen.location || "N/A"}</td>
                                            <td>
                                                <span style={{ backgroundColor: '#F3F4F6', color: '#374151', padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 500, fontFamily: 'monospace' }}>
                                                    {citizen.bot_state}
                                                </span>
                                            </td>
                                            <td style={{ fontWeight: 500 }}>
                                                {citizen.language === 'KN' ? 'ಕನ್ನಡ (KN)' : citizen.language === 'EN' ? 'English (EN)' : citizen.language}
                                            </td>
                                            <td style={{ fontWeight: 500, color: citizen.service !== 'None' ? 'var(--primary)' : 'var(--text-muted)' }}>
                                                {citizen.service}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                )}

                {/* Services Page */}
                {activeTab === 'services' && (
                    <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                            <div>
                                <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Active Government Services Repo</h2>
                                <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '4px' }}>Service parameters and document requirements currently configured in the database.</p>
                            </div>
                            <button onClick={fetchServices} className="action-btn" style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: 'white', color: 'var(--text-main)', border: '1px solid var(--border)' }}>
                                Refresh Services
                            </button>
                        </div>

                        {servicesLoading ? (
                            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading services list...</div>
                        ) : (
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '24px' }}>
                                {services.length === 0 ? (
                                    <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '40px', color: 'var(--text-muted)', backgroundColor: 'white', border: '1px solid var(--border)', borderRadius: '12px' }}>
                                        No services registered in the database.
                                    </div>
                                ) : services.map((svc) => (
                                    <div key={svc.id} style={{ backgroundColor: 'white', border: '1px solid var(--border)', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                        <div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                                <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)' }}>{svc.name_en}</h3>
                                                <span style={{ fontSize: '12px', backgroundColor: '#EEF2FF', color: 'var(--primary)', padding: '2px 8px', borderRadius: '20px', fontWeight: 600 }}>ID: {svc.id}</span>
                                            </div>
                                            <h4 style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-muted)', marginTop: '4px' }}>{svc.name_kn}</h4>
                                        </div>

                                        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                                            <h5 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>English Requirements</h5>
                                            <pre style={{ fontFamily: 'inherit', fontSize: '14px', color: 'var(--text-muted)', whiteSpace: 'pre-wrap' }}>
                                                {svc.required_docs_en}
                                            </pre>
                                        </div>

                                        <div style={{ borderTop: '1px dashed var(--border)', paddingTop: '16px' }}>
                                            <h5 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>ಕನ್ನಡ ದಾಖಲೆಗಳು (Kannada Requirements)</h5>
                                            <pre style={{ fontFamily: 'inherit', fontSize: '14px', color: 'var(--text-muted)', whiteSpace: 'pre-wrap' }}>
                                                {svc.required_docs_kn}
                                            </pre>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
