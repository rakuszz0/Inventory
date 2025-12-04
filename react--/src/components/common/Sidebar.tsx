import React from 'react';
import { Nav } from 'react-bootstrap';
import { LinkContainer } from 'react-router-bootstrap';
import { useAuth } from '../../hooks/useAuth';

const Sidebar: React.FC = () => {
  const { user } = useAuth();

  return (
    <Nav className="flex-column bg-light p-3" style={{ minHeight: '100vh' }}>
      <LinkContainer to="/dashboard">
        <Nav.Link>Dashboard</Nav.Link>
      </LinkContainer>
      <LinkContainer to="/inventory">
        <Nav.Link>Inventaris</Nav.Link>
      </LinkContainer>
      {user?.role === 'super_admin' && (
        <LinkContainer to="/users">
          <Nav.Link>Pengguna</Nav.Link>
        </LinkContainer>
      )}
    </Nav>
  );
};

export default Sidebar;