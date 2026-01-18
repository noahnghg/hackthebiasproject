import { useState, useEffect } from 'react'

function Applications({ currentUser, isActive }) {
    const [applications, setApplications] = useState([])
    const [selectedApp, setSelectedApp] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // Refetch when component becomes active or user changes
        if (currentUser?.id && isActive) {
            fetchApplications()
        } else if (!currentUser) {
            setLoading(false)
        }
    }, [currentUser, isActive])

    const fetchApplications = async () => {
        try {
            const response = await fetch(`/api/applications/user/${currentUser.id}`)
            if (response.ok) {
                const data = await response.json()
                setApplications(data)
            }
        } catch (error) {
            console.error('Error fetching applications:', error)
        } finally {
            setLoading(false)
        }
    }

    const getScoreClass = (score) => {
        if (score >= 0.7) return 'high'
        if (score >= 0.4) return 'medium'
        return 'low'
    }

    const formatScore = (score) => {
        return `${(score * 100).toFixed(0)}%`
    }

    return (
        <div className="application route">
            <div className="applicationsList">
                <div className="pageHeader">
                    <h1 className="pageTitle">Your Applications</h1>
                    <p className="pageSubtitle">Track your job applications and scores</p>
                </div>

                {loading ? (
                    <div className="emptyState">
                        <p>Loading applications...</p>
                    </div>
                ) : !currentUser ? (
                    <div className="emptyState">
                        <i className="fa-solid fa-user"></i>
                        <h3>No user profile</h3>
                        <p>Upload a resume on the Profile page to get started</p>
                    </div>
                ) : applications.length === 0 ? (
                    <div className="emptyState">
                        <i className="fa-solid fa-file-lines"></i>
                        <h3>No applications yet</h3>
                        <p>Apply to jobs to see your applications here</p>
                    </div>
                ) : (
                    applications.map((app) => (
                        <div
                            key={app.id}
                            className={`applicationCard ${selectedApp?.id === app.id ? 'active' : ''}`}
                            onClick={() => setSelectedApp(app)}
                        >
                            <div className="applicationJob">{app.job_title}</div>
                            <div className="applicationCompany">{app.job_company}</div>
                            <span className={`applicationScore ${getScoreClass(app.score)}`}>
                                Match: {formatScore(app.score)}
                            </span>
                        </div>
                    ))
                )}
            </div>

            <div className="scoreSection">
                <h3 className="scoreSectionTitle">Application Details</h3>
                {selectedApp ? (
                    <div className="scoreBreakdown">
                        <div className="scoreItem">
                            <div className="scoreItemLabel">Overall Match</div>
                            <div className={`scoreItemValue ${getScoreClass(selectedApp.score)}`}>
                                {formatScore(selectedApp.score)}
                            </div>
                        </div>
                        <div className="scoreItem">
                            <div className="scoreItemLabel">Position</div>
                            <div className="scoreItemValue" style={{ fontSize: '16px' }}>
                                {selectedApp.job_title}
                            </div>
                        </div>
                        <div className="scoreItem">
                            <div className="scoreItemLabel">Company</div>
                            <div className="scoreItemValue" style={{ fontSize: '16px' }}>
                                {selectedApp.job_company}
                            </div>
                        </div>
                        <div className="scoreItem">
                            <div className="scoreItemLabel">Description</div>
                            <div className="scoreItemValue" style={{ fontSize: '14px', lineHeight: '1.4' }}>
                                {selectedApp.job_description}
                            </div>
                        </div>
                        <div className="scoreItem">
                            <div className="scoreItemLabel">Requirements</div>
                            <div className="scoreItemValue" style={{ fontSize: '14px', lineHeight: '1.4' }}>
                                {selectedApp.job_requirements}
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="emptyState">
                        <p>Select an application to see details</p>
                    </div>
                )}
            </div>
        </div>
    )
}

export default Applications
