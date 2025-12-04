import React from 'react';
import { Spinner } from 'react-bootstrap';

interface LoadingProps {
  message?: string;
}

const Loading: React.FC<LoadingProps> = ({ message = 'Loading...' }) => {
  return (
    <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
      <div className="text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">{message}</span>
        </Spinner>
        <p className="mt-2">{message}</p>
      </div>
    </div>
  );
};

export default Loading;