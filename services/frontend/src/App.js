import { Toolbar } from '@mui/material';
import React, { useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import AppAppBar from './components/AppAppBar';
import BackgroundWrapper from './components/BackgroundWrapper';
import { AuthProvider } from './context/AuthContext';
import CreatePostPage from './pages/CreatePostPage';
import CreateProblemPage from './pages/CreateProblemPage';
import HomePage from './pages/HomePage';
import LoginSide from './pages/LoginSide';
import PostDetail from './pages/PostDetail';
import ProblemDetail from './pages/ProblemDetail';
import ProblemsPage from './pages/ProblemsPage';
import ProfilePage from './pages/ProfilePage';
import RegisterSide from './pages/RegisterSide';
import SolutionDetail from './pages/SolutionDetail';
import TagsPage from './pages/TagsPage';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  return (
    <>
      <AuthProvider>
        <AppAppBar isAuthenticated={isAuthenticated} />

        <BackgroundWrapper>
          <Toolbar />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginSide setIsAuthenticated={setIsAuthenticated} />} />
            <Route path="/register" element={<RegisterSide />} />
            <Route path="/problems" element={<ProblemsPage />} />
            <Route path="/problems/create" element={<CreateProblemPage />} />
            <Route path="/problems/:problemId" element={<ProblemDetail />} />
            <Route path="/posts/create" element={<CreatePostPage />} />
            <Route path="/posts/:postId" element={<PostDetail />} />
            <Route path="/profile/:userId?" element={<ProfilePage />} />
            <Route path="/tags" element={<TagsPage />} />
            <Route path="/solutions/:solution_id" element={<SolutionDetail />} />

          </Routes>
        </BackgroundWrapper>
      </AuthProvider>
    </>
  );
};

export default App;
