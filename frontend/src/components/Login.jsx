import { useState } from 'react'

function Login({ onLoginSuccess }) {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [isSignUp, setIsSignUp] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        if (!email || !password) {
            setError('Please fill in all fields')
            setLoading(false)
            return
        }

        try {
            const endpoint = isSignUp ? '/api/auth/sign-up' : '/api/auth/sign-in'
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            })

            const data = await response.json()

            if (!response.ok) {
                setError(data.detail || 'Authentication failed')
                setLoading(false)
                return
            }

            // Fetch full user profile
            const userResponse = await fetch(`/api/users/${data.user_id}`)
            if (userResponse.ok) {
                const userData = await userResponse.json()
                onLoginSuccess({
                    ...userData,
                    email: data.email
                })
            } else {
                // If user profile doesn't exist yet (new sign up)
                onLoginSuccess({
                    id: data.user_id,
                    email: data.email,
                    skills: '',
                    experience: '',
                    education: ''
                })
            }
        } catch (error) {
            console.error('Auth error:', error)
            setError('Failed to connect to server')
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

                <form className="loginForm" onSubmit={handleSubmit}>
                    <div className="formGroup">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
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
                                <i className="fa-solid fa-spinner fa-spin"></i> {isSignUp ? 'Creating account...' : 'Logging in...'}
                            </>
                        ) : (
                            <>
                                <i className={`fa-solid ${isSignUp ? 'fa-user-plus' : 'fa-sign-in-alt'}`}></i> {isSignUp ? 'Sign Up' : 'Login'}
                            </>
                        )}
                    </button>
                </form>

                <div className="loginFooter">
                    <p>
                        {isSignUp ? 'Already have an account?' : "Don't have an account?"}
                        <button
                            type="button"
                            onClick={() => setIsSignUp(!isSignUp)}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: 'var(--primary-blue)',
                                cursor: 'pointer',
                                marginLeft: '4px',
                                fontWeight: '600'
                            }}
                        >
                            {isSignUp ? 'Login' : 'Sign Up'}
                        </button>
                    </p>
                    <p style={{ marginTop: '8px', fontSize: '11px' }}>
                        Demo: test@example.com / password123
                    </p>
                </div>
            </div>
        </div>
    )
}

export default Login
