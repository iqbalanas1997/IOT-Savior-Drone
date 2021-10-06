import ScrollToBottom from 'react-scroll-to-bottom'

export default function MissionLog({missionLogList}) {
    return(
        <div>
            <h2>Mission Log</h2>
            <ScrollToBottom debug={false} className='mission-log'>
                <ul>{missionLogList}</ul>
            </ScrollToBottom>
        </div>
    )
}
