import { useState } from 'react'
import { createPortal } from 'react-dom'

function Sidebar({ onNavigate, activeIndex, onLogout, currentUser }) {
    const [showLogoutModal, setShowLogoutModal] = useState(false)

    const navItems = [
        { name: 'Jobs', icon: 'fa-briefcase' },
        { name: 'Profile', icon: 'fa-user' },
        { name: 'Applications', icon: 'fa-file-lines' },
        { name: 'Track Postings', icon: 'fa-chart-line' }
    ]

    const handleLogoutClick = () => {
        setShowLogoutModal(true)
    }

    const handleConfirmLogout = () => {
        setShowLogoutModal(false)
        onLogout()
    }

    const handleCancelLogout = () => {
        setShowLogoutModal(false)
    }

    const logoutModal = showLogoutModal && createPortal(
        <div className="confirmModalWrapper active" onClick={handleCancelLogout}>
            <div className="confirmModalContent" onClick={(e) => e.stopPropagation()}>
                <div className="confirmModalHeader">
                    <h2 className="confirmModalTitle">Confirm Logout</h2>
                </div>
                <div className="confirmModalBody">
                    <p>Are you sure you want to log out? You will need to log in again to access your account.</p>
                </div>
                <div className="confirmModalActions">
                    <button className="btn btn-secondary" onClick={handleCancelLogout}>
                        Cancel
                    </button>
                    <button className="btn btn-alert" onClick={handleConfirmLogout}>
                        <i className="fa-solid fa-sign-out-alt"></i> Log Out
                    </button>
                </div>
            </div>
        </div>,
        document.body
    )

    return (
        <aside>
            <nav className="menuNav">
                <ul className="mainNav">
                    {navItems.map((item, idx) => (
                        <li
                            key={item.name}
                            className={`navItem ${activeIndex === idx ? 'active' : ''}`}
                            onClick={() => onNavigate(idx)}
                        >
                            <i className={`fa-solid ${item.icon}`}></i>
                            {item.name}
                        </li>
                    ))}
                </ul>

                <div className="sidebarBottom">
                    <div className="profilebanner">
                        <div className="bannerWrapper">
                            <div className="userProfilePic">
                                <i className="fa-solid fa-user"></i>
                            </div>
                            <div className="userName">{currentUser?.username || 'User'}</div>
                        </div>
                    </div>
                    <div className="logOutBtn" onClick={handleLogoutClick}>
                        <i className="fa-solid fa-right-from-bracket"></i> Log out
                    </div>
                </div>
            </nav>

            {logoutModal}
        </aside>
    )
}

export default Sidebar
