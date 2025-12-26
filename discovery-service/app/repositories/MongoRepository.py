"""
Base MongoDB Repository with async/await support.
Equivalent to Spring Data's CrudRepository abstract class.
Provides generic CRUD operations using Motor async driver.
"""

import logging
from typing import TypeVar, Generic, List, Optional, Dict, Any
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

from app.exceptions.custom_exceptions import DatabaseError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MongoRepository(Generic[T]):
    """
    Generic MongoDB repository providing async CRUD operations.
    Equivalent to Spring Data CrudRepository<T, ID>.
    
    Usage:
        class UserRepository(MongoRepository[User]):
            def __init__(self, db: Any):
                super().__init__(db, "users", User)
    """
    
    def __init__(self, db: Any, collection_name: str, model_class: type):
        """
        Initialize repository with database, collection name, and model class.
        
        Args:
            db: Motor AsyncDatabase instance
            collection_name: Name of MongoDB collection
            model_class: Pydantic model class for type hints and serialization
        """
        self.db = db
        self.collection: Any = db[collection_name]
        self.model_class = model_class
        self.collection_name = collection_name
    
    async def save(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save (insert or update) a document.
        Equivalent to Spring's save() method.
        
        Args:
            document: Dictionary representation of the document
            
        Returns:
            The inserted/updated document with _id
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            if "_id" in document and document["_id"]:
                # Update existing
                result = await self.collection.replace_one(
                    {"_id": document["_id"]},
                    document,
                    upsert=True
                )
                return document
            else:
                # Insert new
                result = await self.collection.insert_one(document)
                document["_id"] = result.inserted_id
                return document
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error in {self.collection_name}: {e}")
            raise DatabaseError(f"Document with this key already exists")
        except Exception as e:
            logger.error(f"Error saving to {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to save document: {str(e)}")
    
    async def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a document by its ID.
        Equivalent to Spring's findById() method.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        try:
            if not isinstance(doc_id, ObjectId):
                doc_id = ObjectId(doc_id)
            return await self.collection.find_one({"_id": doc_id})
        except Exception as e:
            logger.error(f"Error finding document in {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to retrieve document: {str(e)}")
    
    async def find_all(self) -> List[Dict[str, Any]]:
        """
        Find all documents in the collection.
        Equivalent to Spring's findAll() method.
        
        Returns:
            List of all documents
        """
        try:
            cursor = self.collection.find({})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error finding all documents in {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to retrieve documents: {str(e)}")
    
    async def find_by_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find documents matching a query.
        Equivalent to Spring's findBy*() custom finder methods.
        
        Args:
            query: MongoDB query filter
            
        Returns:
            List of matching documents
        """
        try:
            cursor = self.collection.find(query)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error querying {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to query documents: {str(e)}")
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single document matching the query.
        
        Args:
            query: MongoDB query filter
            
        Returns:
            First matching document or None
        """
        try:
            return await self.collection.find_one(query)
        except Exception as e:
            logger.error(f"Error finding one in {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to retrieve document: {str(e)}")
    
    async def delete_by_id(self, doc_id: str) -> bool:
        """
        Delete a document by its ID.
        Equivalent to Spring's deleteById() method.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if document was deleted, False if not found
        """
        try:
            if not isinstance(doc_id, ObjectId):
                doc_id = ObjectId(doc_id)
            result = await self.collection.delete_one({"_id": doc_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting from {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to delete document: {str(e)}")
    
    async def delete_by_query(self, query: Dict[str, Any]) -> int:
        """
        Delete documents matching a query.
        
        Args:
            query: MongoDB query filter
            
        Returns:
            Number of deleted documents
        """
        try:
            result = await self.collection.delete_many(query)
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting from {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to delete documents: {str(e)}")
    
    async def exists(self, query: Dict[str, Any]) -> bool:
        """
        Check if a document matching the query exists.
        Equivalent to Spring's exists() method.
        
        Args:
            query: MongoDB query filter
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            return await self.collection.find_one(query) is not None
        except Exception as e:
            logger.error(f"Error checking existence in {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to check document existence: {str(e)}")
    
    async def count(self, query: Dict[str, Any] = None) -> int:
        """
        Count documents matching the query.
        Equivalent to Spring's count() method.
        
        Args:
            query: MongoDB query filter (optional, defaults to all)
            
        Returns:
            Number of matching documents
        """
        try:
            if query is None:
                query = {}
            return await self.collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting in {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to count documents: {str(e)}")
    
    async def update_by_id(self, doc_id: str, update_fields: Dict[str, Any]) -> bool:
        """
        Update specific fields of a document by ID.
        
        Args:
            doc_id: Document ID
            update_fields: Fields to update
            
        Returns:
            True if document was updated, False if not found
        """
        try:
            if not isinstance(doc_id, ObjectId):
                doc_id = ObjectId(doc_id)
            result = await self.collection.update_one(
                {"_id": doc_id},
                {"$set": update_fields}
            )
            return result.matched_count > 0
        except Exception as e:
            logger.error(f"Error updating in {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to update document: {str(e)}")
    
    async def create_index(self, field_name: str, unique: bool = False):
        """
        Create an index on a field.
        
        Args:
            field_name: Field to index
            unique: Whether the index should be unique
        """
        try:
            index_options = {"unique": unique} if unique else {}
            await self.collection.create_index(field_name, **index_options)
            logger.info(f"Created index on {field_name} in {self.collection_name}")
        except Exception as e:
            logger.error(f"Error creating index in {self.collection_name}: {e}")
