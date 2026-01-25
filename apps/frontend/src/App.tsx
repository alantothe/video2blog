import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './HomePage'
import ArticleTypesPage from './ArticleTypesPage'
import ArticlesPage from './ArticlesPage'
import ImagePipelinePage from './ImagePipelinePage'
import './styles.css'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/articles" element={<ArticlesPage />} />
          <Route path="/article-types" element={<ArticleTypesPage />} />
          <Route path="/image-pipeline" element={<ImagePipelinePage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
