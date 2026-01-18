import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Jobs from './components/Jobs'
import Profile from './components/Profile'
import Applications from './components/Applications'
import TrackPostings from './components/TrackPostings'
import Login from './components/Login'
import './index.css'

function App() {
    const [activeRoute, setActiveRoute] = useState(0)
    const [currentUser, setCurrentUser] = useState(null)
    const [isLoggedIn, setIsLoggedIn] = useState(false)

    useEffect(() => {
        // Check if user exists (for demo, using test-user-001)
        checkUser()
    }, [])

    const checkUser = async () => {
        try {
            const response = await fetch('/api/users/test-user-001')
            if (response.ok) {
                const data = await response.json()
                setCurrentUser(data)
                setIsLoggedIn(true)
            }
        } catch (error) {
            console.log('No existing user found')
        }
    }

    const handleLoginSuccess = (userData) => {
        setCurrentUser(userData)
        setIsLoggedIn(true)
        setActiveRoute(0)
    }

    const handleLogout = () => {
        setCurrentUser(null)
        setIsLoggedIn(false)
        setActiveRoute(0)
    }

    if (!isLoggedIn) {
        return <Login onLoginSuccess={handleLoginSuccess} />
    }

    return (
        <>
            <main>
                <Sidebar
                    onNavigate={setActiveRoute}
                    activeIndex={activeRoute}
                    onLogout={handleLogout}
                    currentUser={currentUser}
                />
                <div className="mainContentWrapper">
                    <div
                        className="routes"
                        style={{ transform: `translateX(-${activeRoute * (100 / 4)}%)` }}
                    >
                        <Jobs currentUser={currentUser} />
                        <Profile currentUser={currentUser} setCurrentUser={setCurrentUser} />
                        <Applications currentUser={currentUser} isActive={activeRoute === 2} />
                        <TrackPostings currentUser={currentUser} isActive={activeRoute === 3} />
                    </div>
                </div>
            </main>
        </>
    )
}

export default App

