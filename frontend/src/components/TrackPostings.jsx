import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'

function TrackPostings({ currentUser }) {
    const [postedJobs, setPostedJobs] = useState([
        {
            id: 1,
            title: 'Senior React Developer',
            description: 'Build scalable web applications using React and modern JavaScript',
            applicationCount: 12,
            expanded: false,
            applicants: [
                { id: 101, name: 'Applicant 1', matchScore: 0.92 },
                { id: 102, name: 'Applicant 2', matchScore: 0.87 },
                { id: 103, name: 'Applicant 3', matchScore: 0.78 },
                { id: 104, name: 'Applicant 4', matchScore: 0.65 },
            ]
        },
        {
            id: 2,
            title: 'Full Stack Developer',
            description: 'Develop end-to-end solutions with React, Node.js, and MongoDB',
            applicationCount: 8,
            expanded: false,
            applicants: [
                { id: 201, name: 'Applicant 5', matchScore: 0.88 },
                { id: 202, name: 'Applicant 6', matchScore: 0.82 },
            ]
        }
    ])

    const [selectedApplicant, setSelectedApplicant] = useState(null)
    const [showApplicantPanel, setShowApplicantPanel] = useState(false)

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
        if (score >= 0.8) return 'high'
        if (score >= 0.6) return 'medium'
        return 'low'
    }

    const applicantPanel = showApplicantPanel && selectedApplicant && createPortal(
        <div className="applicantPanelWrapper active" onClick={handleClosePanel}>
            <div className="applicantPanelContent" onClick={(e) => e.stopPropagation()}>
                <button className="panelClose" onClick={handleClosePanel}>
                    <i className="fa-solid fa-xmark"></i>
                </button>

                <div className="panelHeader">
                    <div>
                        <h2 className="panelTitle">{selectedApplicant.name}</h2>
                        <span className={`panelScore ${getScoreClass(selectedApplicant.matchScore)}`}>
                            {(selectedApplicant.matchScore * 100).toFixed(0)}% Match
                        </span>
                    </div>
                </div>

                <div className="panelBody">
                    {/* Skills Section */}
                    <div className="collapsibleSection expanded">
                        <div className="sectionHeader">
                            <h3><i className="fa-solid fa-code"></i> Skills</h3>
                            <i className="fa-solid fa-chevron-up"></i>
                        </div>
                        <div className="sectionContent">
                            <div className="skillsPills">
                                <span className="skillPill">React</span>
                                <span className="skillPill">JavaScript</span>
                                <span className="skillPill">TypeScript</span>
                                <span className="skillPill">Node.js</span>
                                <span className="skillPill">MongoDB</span>
                                <span className="skillPill">REST APIs</span>
                                <span className="skillPill">Git</span>
                            </div>
                        </div>
                    </div>

                    {/* Experience Section */}
                    <div className="collapsibleSection expanded">
                        <div className="sectionHeader">
                            <h3><i className="fa-solid fa-briefcase"></i> Experience</h3>
                            <i className="fa-solid fa-chevron-up"></i>
                        </div>
                        <div className="sectionContent">
                            <p>5+ years of experience in full-stack web development with focus on React and Node.js. Proven track record of building scalable applications and leading development teams. Strong understanding of modern development practices and agile methodologies.</p>
                        </div>
                    </div>

                    {/* Education Section */}
                    <div className="collapsibleSection">
                        <div className="sectionHeader">
                            <h3><i className="fa-solid fa-graduation-cap"></i> Education</h3>
                            <i className="fa-solid fa-chevron-down"></i>
                        </div>
                    </div>
                </div>

                <div className="panelActions">
                    <button className="btn btn-primary">
                        <i className="fa-solid fa-envelope"></i> Contact
                    </button>
                </div>
            </div>
        </div>,
        document.body
    )

    return (
        <div className="trackPostings route">
            <div className="pageHeader">
                <h1 className="pageTitle">Track Your Job Postings</h1>
                <p className="pageSubtitle">Monitor applications and track candidate matches</p>
            </div>

            <div className="postedJobsContainer">
                {postedJobs.map((job) => (
                    <div key={job.id} className="postedJob">
                        <div 
                            className="jobPostHeader"
                            onClick={() => toggleJobExpanded(job.id)}
                        >
                            <div className="jobPostInfo">
                                <h3 className="jobPostTitle">{job.title}</h3>
                                <p className="jobPostDesc">{job.description}</p>
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
                                {job.applicants.map((applicant) => (
                                    <div
                                        key={applicant.id}
                                        className="applicantItem"
                                        onClick={() => handleApplicantClick(applicant)}
                                    >
                                        <div className="applicantInfo">
                                            <div className="applicantAvatar">
                                                <i className="fa-solid fa-user"></i>
                                            </div>
                                            <span className="applicantLabel">Applicant {applicant.id % 100}</span>
                                        </div>
                                        <span className={`applicationScore ${getScoreClass(applicant.matchScore)}`}>
                                            {(applicant.matchScore * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {applicantPanel}
        </div>
    )
}

export default TrackPostings
