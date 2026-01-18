import { useState } from 'react'

function Login({ onLoginSuccess }) {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleLogin = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        if (!username || !password) {
            setError('Please fill in all fields')
            setLoading(false)
            return
        }

        // Hardcoded login check
        if (username === 'johndoe' && password === 'Password1') {
            const userData = {
                id: 'user-001',
                username: username,
                email: 'johndoe@example.com',
                skills: 'React, JavaScript, TypeScript, Node.js',
                experience: 'Senior software engineer with 8+ years of experience building scalable applications.',
                education: 'B.S. Computer Science'
            }
            onLoginSuccess(userData)
        } else {
            setError('Invalid username or password. Try: johndoe / Password1')
        }
        setLoading(false)
    }

    return (
        <div className="loginContainer">
            <div className="loginCard">
                <div className="loginHeader">
                    <h1 className="loginTitle">HRight</h1>
                    <p className="loginSubtitle">Fair Job Matching Platform</p>
                </div>

                <form className="loginForm" onSubmit={handleLogin}>
                    <div className="formGroup">
                        <label htmlFor="username">Username</label>
                        <input
                            id="username"
                            type="text"
                            placeholder="Enter your username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="formInput"
                            disabled={loading}
                        />
                    </div>

                    <div className="formGroup">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="formInput"
                            disabled={loading}
                        />
                    </div>

                    {error && <div className="loginError">{error}</div>}

                    <button
                        type="submit"
                        className="loginBtn"
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <i className="fa-solid fa-spinner fa-spin"></i> Logging in...
                            </>
                        ) : (
                            <>
                                <i className="fa-solid fa-sign-in-alt"></i> Login
                            </>
                        )}
                    </button>
                </form>

                <div className="loginFooter">
                    <p>Demo credentials: Use any username/password for testing</p>
                </div>
            </div>
        </div>
    )
}

export default Login
