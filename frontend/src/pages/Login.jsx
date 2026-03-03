import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import API_BASE from '../api';

export default function Login() {
    const [username, setUsername] = useState('admin');
    const [password, setPassword] = useState('password123');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            // Connect to the isolated staff DB logic in FastAPI
            const res = await axios.post(`${API_BASE}/api/staff/login`, { username, password });
            if (res.data.success) {
                localStorage.setItem('staffToken', res.data.token);
                localStorage.setItem('staffUser', JSON.stringify(res.data.user));
                navigate('/dashboard');
            }
        } catch (err) {
            setError('Invalid username or password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-color)' }}>
            <div style={{ background: 'white', padding: '40px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', width: '100%', maxWidth: '400px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '32px' }}>
                    <div style={{ background: 'var(--primary)', color: 'white', padding: '6px', borderRadius: '8px' }}>
                        <span style={{ fontWeight: 800, fontSize: '20px' }}>1</span>
                    </div>
                    <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--primary)' }}>OneTrip</h1>
                </div>

                <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '8px', textAlign: 'center' }}>Staff Portal</h2>
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginBottom: '24px', fontSize: '14px' }}>Log in to view secure tokens and complete citizens' appointments.</p>

                {error && <div style={{ backgroundColor: '#FEE2E2', color: '#DC2626', padding: '12px', borderRadius: '8px', marginBottom: '20px', fontSize: '14px', textAlign: 'center' }}>{error}</div>}

                <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                        <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>Staff ID</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '14px' }}
                            required
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>Security Code</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '14px' }}
                            required
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        style={{ width: '100%', padding: '12px', backgroundColor: 'var(--primary)', color: 'white', border: 'none', borderRadius: '8px', fontWeight: '600', marginTop: '8px', cursor: 'pointer', opacity: loading ? 0.7 : 1 }}
                    >
                        {loading ? 'Authenticating...' : 'Secure Login'}
                    </button>
                </form>
            </div>
        </div>
    );
}
