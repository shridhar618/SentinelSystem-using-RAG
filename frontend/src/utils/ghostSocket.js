import { io } from 'socket.io-client'

let ghostSocket = null
let adminToken = null

export function getGhostSocket() {
  if (!ghostSocket) {
    ghostSocket = io('/', {
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    })
    // admin_room membership is lost on reconnect, so re-authenticate.
    ghostSocket.on('connect', () => {
      if (adminToken) ghostSocket.emit('join_admin_room', { token: adminToken })
    })
  }

  return ghostSocket
}

/**
 * Join the admin-only Ghost Mode room. The server verifies the JWT and that
 * the account is an administrator before granting membership (it previously
 * accepted anyone), so the token must be supplied.
 */
export function joinGhostAdminRoom(token) {
  const socket = getGhostSocket()
  adminToken = token || localStorage.getItem('token')
  if (adminToken) socket.emit('join_admin_room', { token: adminToken })
  return socket
}
