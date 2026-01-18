import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'

function TrackPostings({ currentUser, isActive }) {
    const [postedJobs, setPostedJobs] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedApplicant, setSelectedApplicant] = useState(null)
    const [showApplicantPanel, setShowApplicantPanel] = useState(false)

    useEffect(() => {
        // Refetch when component becomes active or user changes
        if (currentUser?.id && isActive) {
            fetchPostedJobs()
        } else if (!currentUser) {
            setLoading(false)
        }
    }, [currentUser, isActive])

    const fetchPostedJobs = async () => {
        try {
            // Fetch jobs posted by the current user
            const response = await fetch(`/api/users/${currentUser.id}/jobs`)
            if (response.ok) {
                const jobs = await response.json()

                // For each job, fetch its applications
                const jobsWithApplicants = await Promise.all(
                    jobs.map(async (job) => {
                        const appResponse = await fetch(`/api/applications/job/${job.id}`)
                        const applicants = appResponse.ok ? await appResponse.json() : []
                        return {
                            ...job,
                            expanded: false,
                            applicants: applicants,
                            applicationCount: applicants.length
                        }
                    })
                )
                setPostedJobs(jobsWithApplicants)
            }
        } catch (error) {
            console.error('Error fetching posted jobs:', error)
        } finally {
            setLoading(false)
        }
    }

    const toggleJobExpanded = (jobId) => {
        setPostedJobs(prev => prev.map(job =>
            job.id === jobId ? { ...job, expanded: !job.expanded } : job
        ))
    }

    const handleApplicantClick = (applicant) => {
        setSelectedApplicant(applicant)
        setShowApplicantPanel(true)
    }

    const handleClosePanel = () => {
        setShowApplicantPanel(false)
        setSelectedApplicant(null)
    }

    const getScoreClass = (score) => {
        if (score >= 0.7) return 'high'
        if (score >= 0.4) return 'medium'
        return 'low'
    }

    // Parse skills into array
    const parseSkills = (skillsStr) => {
        if (!skillsStr) return []
        return skillsStr.split(',').map(s => s.trim()).filter(s => s)
    }

    const applicantPanel = showApplicantPanel && selectedApplicant && createPortal(
        <div className="applicantPanelWrapper active" onClick={handleClosePanel}>
            <div className="applicantPanelContent" onClick={(e) => e.stopPropagation()}>
                <button className="panelClose" onClick={handleClosePanel}>
                    <i className="fa-solid fa-xmark"></i>
                </button>

                <div className="panelHeader">
                    <div>
                        <h2 className="panelTitle">Applicant Profile</h2>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: '4px 0 0 0' }}>
                            {selectedApplicant.user_email}
                        </p>
                    </div>
                    <span className={`panelScore ${getScoreClass(selectedApplicant.score)}`}>
                        {(selectedApplicant.score * 100).toFixed(0)}% Match
                    </span>
                </div>

                <div className="panelBody">
                    {/* Skills Section */}
                    <div className="collapsibleSection expanded">
                        <div className="sectionHeader">
                            <h3><i className="fa-solid fa-code"></i> Skills</h3>
                        </div>
                        <div className="sectionContent">
                            <div className="skillsPills">
                                {parseSkills(selectedApplicant.user_skills).map((skill, idx) => (
                                    <span key={idx} className="skillPill">{skill}</span>
                                ))}
                                {!selectedApplicant.user_skills && (
                                    <p style={{ color: 'var(--text-secondary)' }}>No skills listed</p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Experience Section */}
                    <div className="collapsibleSection expanded">
                        <div className="sectionHeader">
                            <h3><i className="fa-solid fa-briefcase"></i> Experience</h3>
                        </div>
                        <div className="sectionContent">
                            <p style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--dark-navy)' }}>
                                {selectedApplicant.user_experience || 'No experience listed'}
                            </p>
                        </div>
                    </div>

                    {/* Education Section */}
                    <div className="collapsibleSection expanded">
                        <div className="sectionHeader">
                            <h3><i className="fa-solid fa-graduation-cap"></i> Education</h3>
                        </div>
                        <div className="sectionContent">
                            <p style={{ fontSize: '14px', color: 'var(--dark-navy)' }}>
                                {selectedApplicant.user_education || 'No education listed'}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="panelActions">
                    <button className="btn btn-primary">
                        <i className="fa-solid fa-envelope"></i> Contact Applicant
                    </button>
                </div>
            </div>
        </div>,
        document.body
    )

    if (loading) {
        return (
            <div className="trackPostings route">
                <div className="pageHeader">
                    <h1 className="pageTitle">Track Your Job Postings</h1>
                    <p className="pageSubtitle">Loading your postings...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="trackPostings route">
            <div className="pageHeader">
                <h1 className="pageTitle">Track Your Job Postings</h1>
                <p className="pageSubtitle">Monitor applications and track candidate matches</p>
            </div>

            {!currentUser ? (
                <div className="emptyState">
                    <i className="fa-solid fa-user"></i>
                    <h3>Not logged in</h3>
                    <p>Please log in to see your job postings</p>
                </div>
            ) : postedJobs.length === 0 ? (
                <div className="emptyState">
                    <i className="fa-solid fa-briefcase"></i>
                    <h3>No postings yet</h3>
                    <p>Post a job from the Jobs page to track applications here</p>
                </div>
            ) : (
                <div className="postedJobsContainer">
                    {postedJobs.map((job) => (
                        <div key={job.id} className="postedJob">
                            <div
                                className="jobPostHeader"
                                onClick={() => toggleJobExpanded(job.id)}
                            >
                                <div className="jobPostInfo">
                                    <h3 className="jobPostTitle">{job.title}</h3>
                                    <p className="jobPostDesc">{job.company}</p>
                                </div>
                                <div className="jobPostStats">
                                    <div className="appBadge">
                                        <i className="fa-solid fa-users"></i>
                                        <span>{job.applicationCount} Applications</span>
                                    </div>
                                    <i className={`fa-solid ${job.expanded ? 'fa-chevron-up' : 'fa-chevron-down'}`}></i>
                                </div>
                            </div>

                            {job.expanded && (
                                <div className="applicantsList">
                                    {job.applicants.length === 0 ? (
                                        <div style={{ padding: 'var(--space-lg)', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                            No applications yet
                                        </div>
                                    ) : (
                                        job.applicants.map((applicant) => (
                                            <div
                                                key={applicant.id}
                                                className="applicantItem"
                                                onClick={() => handleApplicantClick(applicant)}
                                            >
                                                <div className="applicantInfo">
                                                    <div className="applicantAvatar">
                                                        <i className="fa-solid fa-user"></i>
                                                    </div>
                                                    <span className="applicantLabel">{applicant.user_email}</span>
                                                </div>
                                                <span className={`applicationScore ${getScoreClass(applicant.score)}`}>
                                                    {(applicant.score * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        ))
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {applicantPanel}
        </div>
    )
}

export default TrackPostings
