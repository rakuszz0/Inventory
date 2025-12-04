import React from 'react';
import { Outlet } from 'react-router-dom';
import { Row, Col } from 'react-bootstrap';
import Header from '../common/Header';
import Sidebar from '../common/Sidebar';

interface MainLayoutProps {
  children?: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <>
      <Header />
      <Row>
        <Col md={2} className="p-0">
          <Sidebar />
        </Col>
        <Col md={10} className="p-4">
          {children || <Outlet />}
        </Col>
      </Row>
    </>
  );
};

export default MainLayout;