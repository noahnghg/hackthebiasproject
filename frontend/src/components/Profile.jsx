import { useState, useEffect } from 'react'

function Profile({ currentUser, setCurrentUser }) {
    const [applications, setApplications] = useState([])
    const [expandedSections, setExpandedSections] = useState({
        skills: true,
        experience: true,
        education: false
    })

    useEffect(() => {
        if (currentUser?.id) {
            fetchApplications()
        }
    }, [currentUser])

    const fetchApplications = async () => {
        try {
            const response = await fetch(`/api/applications/user/${currentUser.id}`)
            if (response.ok) {
                const data = await response.json()
                setApplications(data)
            }
        } catch (error) {
            console.error('Error fetching applications:', error)
        }
    }

    const handleFileUpload = async (e) => {
        const file = e.target.files[0]
        if (!file) return

        const formData = new FormData()
        formData.append('file', file)
        formData.append('user_id', currentUser?.id || 'new-user')

        try {
            const response = await fetch('/api/users/upload-resume', {
                method: 'POST',
                body: formData
            })
            const data = await response.json()
            setCurrentUser(data)
            alert('Resume uploaded successfully!')
        } catch (error) {
            console.error('Error uploading resume:', error)
            alert('Failed to upload resume')
        }
    }

    const getScoreClass = (score) => {
        if (score >= 0.7) return 'high'
        if (score >= 0.4) return 'medium'
        return 'low'
    }

    const toggleSection = (section) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }))
    }

    // Parse skills string into array
    const skillsList = currentUser?.skills
        ? currentUser.skills.split(',').map(s => s.trim()).filter(s => s)
        : []

    // Get experience summary (first 2-3 sentences)
    const experienceSummary = currentUser?.experience
        ? currentUser.experience.split('.').slice(0, 3).join('.') + '.'
        : ''

    return (
        <div className="profile route">
            {/* Profile Preview Section - Top 1/3 */}
            <div className="profilePreview">
                {currentUser?.skills ? (
                    <div className="userInfo">
                        {/* Skills Section - Collapsible */}
                        <div className={`collapsibleSection ${expandedSections.skills ? 'expanded' : ''}`}>
                            <div className="sectionHeader" onClick={() => toggleSection('skills')}>
                                <h3><i className="fa-solid fa-code"></i> Skills</h3>
                                <i className={`fa-solid ${expandedSections.skills ? 'fa-chevron-up' : 'fa-chevron-down'}`}></i>
                            </div>
                            {expandedSections.skills && (
                                <div className="sectionContent">
                                    <div className="skillsPills">
                                        {skillsList.map((skill, idx) => (
                                            <span key={idx} className="skillPill">{skill}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Experience Summary - Collapsible */}
                        <div className={`collapsibleSection ${expandedSections.experience ? 'expanded' : ''}`}>
                            <div className="sectionHeader" onClick={() => toggleSection('experience')}>
                                <h3><i className="fa-solid fa-briefcase"></i> Experience Summary</h3>
                                <i className={`fa-solid ${expandedSections.experience ? 'fa-chevron-up' : 'fa-chevron-down'}`}></i>
                            </div>
                            {expandedSections.experience && (
                                <div className="sectionContent">
                                    <p className="experienceText">{experienceSummary}</p>
                                </div>
                            )}
                        </div>

                        {/* Education - Collapsible */}
                        <div className={`collapsibleSection ${expandedSections.education ? 'expanded' : ''}`}>
                            <div className="sectionHeader" onClick={() => toggleSection('education')}>
                                <h3><i className="fa-solid fa-graduation-cap"></i> Education</h3>
                                <i className={`fa-solid ${expandedSections.education ? 'fa-chevron-up' : 'fa-chevron-down'}`}></i>
                            </div>
                            {expandedSections.education && (
                                <div className="sectionContent">
                                    <p>{currentUser.education}</p>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="uploadPrompt">
                        <label className="uploadArea">
                            <input
                                type="file"
                                accept=".pdf"
                                style={{ display: 'none' }}
                                onChange={handleFileUpload}
                            />
                            <i className="fa-solid fa-cloud-arrow-up"></i>
                            <span>Upload your resume to create your profile</span>
                            <small>PDF files only</small>
                        </label>
                    </div>
                )}
            </div>
        </div>
    )
}

export default Profile
